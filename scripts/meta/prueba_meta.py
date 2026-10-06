"""Prueba de viabilidad con la Graph API de Meta (Fase 1 del plan).

Comprueba, con un token de usuario de prueba, que la cuenta de demo puede:
ver su página de Facebook y su cuenta de Instagram profesional vinculada,
publicar una imagen JPEG y leer las métricas del post.

El token se genera en el Explorador de la API Graph y se guarda en
backend/.env como META_ACCESS_TOKEN (nunca en el chat ni en Git).

Desde la raíz del repo:

    backend/venv/bin/python scripts/meta/prueba_meta.py
        Solo lectura: usuario, permisos concedidos, páginas e Instagram vinculado.

    backend/venv/bin/python scripts/meta/prueba_meta.py --publicar-ig
        Publica la imagen de muestra en Instagram (post REAL y visible).

    backend/venv/bin/python scripts/meta/prueba_meta.py --publicar-fb
        Publica la imagen de muestra en la página de Facebook (post REAL).

    backend/venv/bin/python scripts/meta/prueba_meta.py --metricas-ig MEDIA_ID
        Lee me gusta, comentarios e insights de una publicación de Instagram.

Opciones: --pagina ID para elegir la página si hay varias, --imagen URL para
usar otra imagen pública (debe ser JPEG), --texto para cambiar la descripción.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
GRAPH = "https://graph.facebook.com/v25.0"
IMAGEN_MUESTRA = (
    "https://raw.githubusercontent.com/JasonGomezzz/MarketMind-Voice/"
    "remejora/scripts/meta/muestra-cafe-gemini.jpg"
)
TEXTO_MUESTRA = "Prueba de publicación automática desde NexoMark IA: imagen generada con IA."
PERMISOS_ESPERADOS = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "instagram_basic",
    "instagram_content_publish",
    "instagram_manage_insights",
    "business_management",
]
METRICAS_IG = "likes,comments,shares,saved,reach,views,total_interactions"


def leer_token() -> str:
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    if not token:
        env = ROOT / "backend" / ".env"
        if env.exists():
            for linea in env.read_text().splitlines():
                if linea.startswith("META_ACCESS_TOKEN="):
                    token = linea.split("=", 1)[1].strip().strip('"').strip("'")
    if not token:
        sys.exit("Falta META_ACCESS_TOKEN en backend/.env (no lo pegues en el chat).")
    return token


def graph(metodo: str, ruta: str, token: str, **params) -> dict:
    response = httpx.request(
        metodo, f"{GRAPH}/{ruta}", params={**params, "access_token": token}, timeout=60
    )
    data = response.json() if response.content else {}
    if response.status_code >= 400 or "error" in data:
        error = data.get("error", {})
        sys.exit(
            f"{metodo} /{ruta} → HTTP {response.status_code}: "
            f"{error.get('message', response.text[:300])} "
            f"(code={error.get('code')}, subcode={error.get('error_subcode')})"
        )
    return data


def diagnosticar(token: str) -> list[dict]:
    yo = graph("GET", "me", token, fields="id,name")
    print(f"Usuario: {yo.get('name')} (id {yo.get('id')})")

    concedidos = {
        p["permission"] for p in graph("GET", "me/permissions", token).get("data", [])
        if p.get("status") == "granted"
    }
    print("Permisos:")
    for permiso in PERMISOS_ESPERADOS:
        print(f"  {'OK ' if permiso in concedidos else 'FALTA'} {permiso}")

    paginas = graph(
        "GET", "me/accounts", token,
        fields="id,name,access_token,instagram_business_account{id,username}",
    ).get("data", [])
    if not paginas:
        print("No hay páginas de Facebook visibles con este token.")
    for pagina in paginas:
        ig = pagina.get("instagram_business_account")
        destino = f"Instagram @{ig['username']} (id {ig['id']})" if ig else "sin Instagram vinculado"
        print(f"Página: {pagina['name']} (id {pagina['id']}) → {destino}")
    return paginas


def elegir_pagina(paginas: list[dict], pagina_id: str | None) -> dict:
    if pagina_id:
        pagina = next((p for p in paginas if p["id"] == pagina_id), None)
        if not pagina:
            sys.exit(f"La página {pagina_id} no está entre las visibles con este token.")
        return pagina
    if len(paginas) != 1:
        sys.exit("Hay varias páginas (o ninguna): indica cuál con --pagina ID.")
    return paginas[0]


def publicar_instagram(pagina: dict, imagen: str, texto: str) -> None:
    ig = pagina.get("instagram_business_account")
    if not ig:
        sys.exit("La página no tiene una cuenta de Instagram profesional vinculada.")
    token = pagina["access_token"]

    contenedor = graph("POST", f"{ig['id']}/media", token, image_url=imagen, caption=texto)["id"]
    print(f"Contenedor creado: {contenedor}")
    for _ in range(15):
        estado = graph("GET", contenedor, token, fields="status_code").get("status_code")
        if estado == "FINISHED":
            break
        if estado in ("ERROR", "EXPIRED"):
            sys.exit(f"Meta no pudo procesar la imagen: {estado}")
        time.sleep(2)
    else:
        sys.exit("El contenedor no terminó de procesarse a tiempo; no se publicó.")

    media = graph("POST", f"{ig['id']}/media_publish", token, creation_id=contenedor)["id"]
    detalle = graph("GET", media, token, fields="permalink,timestamp")
    print(f"Publicado en Instagram: media {media}")
    print(f"  {detalle.get('permalink')}  ({detalle.get('timestamp')})")
    print(f"  Métricas después: --metricas-ig {media}")


def publicar_facebook(pagina: dict, imagen: str, texto: str) -> None:
    data = graph("POST", f"{pagina['id']}/photos", pagina["access_token"], url=imagen, caption=texto)
    print(f"Publicado en Facebook: foto {data.get('id')}, post {data.get('post_id')}")


def metricas_instagram(pagina: dict, media_id: str) -> None:
    token = pagina["access_token"]
    basico = graph("GET", media_id, token, fields="like_count,comments_count,permalink,timestamp")
    print(f"Post {basico.get('permalink')}")
    print(f"  me gusta: {basico.get('like_count')}  comentarios: {basico.get('comments_count')}")
    insights = graph("GET", f"{media_id}/insights", token, metric=METRICAS_IG).get("data", [])
    if not insights:
        print("  insights: sin datos todavía (Meta puede tardar hasta 48 h; vacío no es cero)")
    for metrica in insights:
        valor = (metrica.get("values") or [{}])[0].get("value")
        print(f"  {metrica.get('name')}: {valor}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--publicar-ig", action="store_true", help="publica la imagen en Instagram")
    parser.add_argument("--publicar-fb", action="store_true", help="publica la imagen en la página")
    parser.add_argument("--metricas-ig", metavar="MEDIA_ID", help="lee métricas de un post de Instagram")
    parser.add_argument("--pagina", metavar="ID", help="página de Facebook a usar si hay varias")
    parser.add_argument("--imagen", default=IMAGEN_MUESTRA, help="URL pública de una imagen JPEG")
    parser.add_argument("--texto", default=TEXTO_MUESTRA, help="descripción del post")
    args = parser.parse_args()

    token = leer_token()
    paginas = diagnosticar(token)
    if not (args.publicar_ig or args.publicar_fb or args.metricas_ig):
        return

    pagina = elegir_pagina(paginas, args.pagina)
    if args.publicar_ig:
        publicar_instagram(pagina, args.imagen, args.texto)
    if args.publicar_fb:
        publicar_facebook(pagina, args.imagen, args.texto)
    if args.metricas_ig:
        metricas_instagram(pagina, args.metricas_ig)


if __name__ == "__main__":
    main()
