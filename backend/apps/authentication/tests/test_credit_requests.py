"""Solicitudes de créditos con aprobación auditada (adaptado de la rama de Piero)."""

import pytest
from rest_framework.test import APIClient

from apps.authentication.models import CreditRequest, CreditRequestStatus

pytestmark = pytest.mark.django_db
OWN = "/api/auth/credit-requests/"
ADMIN = "/api/admin/credit-requests/"


def _solicitar(client, motivo=""):
    return client.post(OWN, {"motivo": motivo}, format="json")


def test_la_solicitud_se_guarda_y_duplicarla_no_crea_otra(api_client, user_marketero):
    creada = _solicitar(api_client, "Campaña de fin de mes")
    assert creada.status_code == 201
    assert creada.data["success"] is True
    assert creada.data["data"]["solicitud"]["estado"] == "pendiente"
    assert creada.data["data"]["solicitud"]["motivo"] == "Campaña de fin de mes"

    repetida = _solicitar(api_client)
    assert repetida.status_code == 200
    assert "pendiente" in repetida.data["message"]
    assert CreditRequest.objects.filter(solicitante=user_marketero).count() == 1

    mias = api_client.get(OWN).data["data"]
    assert len(mias["solicitudes"]) == 1
    assert mias["pendiente"]["id"] == creada.data["data"]["solicitud"]["id"]
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 10  # pedir no suma nada


def test_aprobar_suma_una_vez_y_queda_auditado(api_client, superadmin_client, user_marketero, superadmin):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    url = f"{ADMIN}{pk}/"

    response = superadmin_client.patch(url, {"estado": "aprobada", "creditos": 50, "nota": "Ok"}, format="json")

    assert response.status_code == 200
    assert response.data["success"] is True
    assert superadmin_client.patch(url, {"estado": "aprobada", "creditos": 50}, format="json").status_code == 409
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 60
    item = CreditRequest.objects.get(pk=pk)
    assert item.estado == CreditRequestStatus.APROBADA
    assert item.resuelta_por == superadmin
    assert item.resuelta_en is not None
    assert item.creditos_otorgados == 50
    assert item.saldo_resultante == 60
    assert item.nota_resolucion == "Ok"
    assert response.data["data"]["solicitud"]["resuelta_por"] == superadmin.nombre
    # Resuelta la anterior, puede pedir otra.
    assert _solicitar(api_client).status_code == 201


def test_aprobar_no_pisa_un_cobro_concurrente(api_client, superadmin_client, user_marketero):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    # El saldo cambia en BD después de que el objeto en memoria se cargó.
    type(user_marketero).objects.filter(pk=user_marketero.pk).update(tokens_disponibles=3)
    superadmin_client.patch(f"{ADMIN}{pk}/", {"estado": "aprobada", "creditos": 5}, format="json")
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 8


def test_rechazar_conserva_el_saldo(api_client, superadmin_client, user_marketero):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    response = superadmin_client.patch(f"{ADMIN}{pk}/", {"estado": "rechazada", "nota": "Sin presupuesto"}, format="json")
    assert response.status_code == 200
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 10
    item = CreditRequest.objects.get(pk=pk)
    assert item.estado == CreditRequestStatus.RECHAZADA
    assert item.creditos_otorgados == 0
    assert item.saldo_resultante is None
    assert item.resuelta_en is not None


@pytest.mark.parametrize("payload", [
    {"estado": "aprobada"},
    {"estado": "aprobada", "creditos": 0},
    {"estado": "aprobada", "creditos": 10001},
    {"estado": "aprobada", "creditos": 1.5},
    {"estado": "aprobada", "creditos": True},
    {"estado": "pendiente"},
    {"estado": "rechazada", "creditos": 10},
    {},
])
def test_decision_invalida_no_cambia_la_solicitud(api_client, superadmin_client, user_marketero, payload):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    response = superadmin_client.patch(f"{ADMIN}{pk}/", payload, format="json")
    assert response.status_code == 400
    assert response.data["success"] is False
    assert CreditRequest.objects.get(pk=pk).estado == CreditRequestStatus.PENDIENTE
    user_marketero.refresh_from_db()
    assert user_marketero.tokens_disponibles == 10


def test_permisos_por_rol(api_client, superadmin_client, cliente):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    assert api_client.get(ADMIN).status_code == 403
    assert api_client.patch(f"{ADMIN}{pk}/", {"estado": "aprobada", "creditos": 100}, format="json").status_code == 403
    # El superadmin no se pide créditos a sí mismo (no podría aprobarse solo).
    assert superadmin_client.post(OWN, {}, format="json").status_code == 403
    listado = superadmin_client.get(ADMIN).data["data"]
    assert len(listado["solicitudes"]) == 1
    assert listado["pendientes"] == 1
    anonimo = APIClient()
    assert anonimo.post(OWN, {}, format="json").status_code == 401
    del_cliente = APIClient()
    del_cliente.force_authenticate(user=cliente)
    assert del_cliente.post(OWN, {}, format="json").status_code == 403
    assert del_cliente.get(OWN).status_code == 403


def test_filtro_por_estado(api_client, superadmin_client):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    superadmin_client.patch(f"{ADMIN}{pk}/", {"estado": "rechazada"}, format="json")
    _solicitar(api_client)
    assert len(superadmin_client.get(ADMIN, {"estado": "pendiente"}).data["data"]["solicitudes"]) == 1
    assert len(superadmin_client.get(ADMIN, {"estado": "rechazada"}).data["data"]["solicitudes"]) == 1
    assert superadmin_client.get(ADMIN, {"estado": "otro"}).status_code == 400


def test_no_se_resuelve_la_solicitud_de_una_cuenta_suspendida(api_client, superadmin_client, user_marketero):
    pk = _solicitar(api_client).data["data"]["solicitud"]["id"]
    user_marketero.is_active = False
    user_marketero.save(update_fields=["is_active"])
    response = superadmin_client.patch(f"{ADMIN}{pk}/", {"estado": "aprobada", "creditos": 100}, format="json")
    assert response.status_code == 409
    assert CreditRequest.objects.get(pk=pk).estado == CreditRequestStatus.PENDIENTE


def test_solicitud_inexistente_404(superadmin_client):
    assert superadmin_client.patch(f"{ADMIN}999/", {"estado": "rechazada"}, format="json").status_code == 404


def test_motivo_demasiado_largo_400(api_client):
    assert _solicitar(api_client, "x" * 301).status_code == 400
