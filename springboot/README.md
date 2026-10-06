****# MarketMind — Spring Boot (Bloque Usuario)

API REST de cara al cliente final. Puerto local `8081` (8080 dentro de Docker).
Usa una sola instancia; consulta [ejecución local](../LOCAL_DEVELOPMENT.md).
Convive con Django (puerto `8000`) sobre la misma PostgreSQL.

## Regla de oro

> **NUNCA** cambiar `spring.jpa.hibernate.ddl-auto` a `update` o `create`.
> Django es el dueño absoluto del schema. Spring Boot solo valida (`validate`).
> Cambiar esto destruiría o modificaría tablas en producción.

## Responsabilidades

| Spring Boot hace | Spring Boot NO hace |
|-----------------|---------------------|
| Leer campañas y usuarios | Crear/modificar el schema |
| Escribir solo el campo `estado` | Emitir tokens JWT |
| Validar JWT emitidos por Django | Gestionar migraciones |
| Aprobar / rechazar campañas | Llamar a n8n o Gemini |

## Variables de entorno requeridas

```env
DB_HOST=localhost          # postgres (Docker) o localhost (local)
DB_PORT=5435               # 5435 fuera de Docker, 5432 dentro
DB_NAME=marketmind_db
DB_USER=marketmind_user
DB_PASSWORD=localpass123
SECRET_KEY=<mismo SECRET_KEY que usa Django>
SPRING_PROFILES_ACTIVE=dev
```

## Correr localmente (fuera de Docker)

Prerequisito: Django debe tener aplicada la migración `0003_campaign_version`.

```bash
cd springboot

# Con Maven instalado:
DB_HOST=localhost DB_PORT=5435 DB_NAME=marketmind_db \
DB_USER=marketmind_user DB_PASSWORD=localpass123 \
SECRET_KEY=<secret_key> \
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# O exportando las variables primero:
export DB_HOST=localhost DB_PORT=5435 ...
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

El servidor arranca en `http://localhost:8081`.
Al iniciar verás el validate de Hibernate — si ves DDL (`CREATE TABLE`, `ALTER TABLE`) hay un error de configuración.

## Correr con Docker Compose

```bash
# Desde la raíz del repo:
docker compose up -d postgres redis
docker compose up springboot
```

## Abrir en IntelliJ IDEA

1. `File → Open` → seleccionar la carpeta `springboot/` (no la raíz del repo)
2. IntelliJ detecta el `pom.xml` y configura Maven automáticamente
3. Importar como proyecto Maven
4. Configurar SDK: Java 21
5. Para correr: botón Run en `MarketMindApplication.java`
6. Agregar las variables de entorno en `Run/Debug Configurations → Environment variables`

IntelliJ Community Edition es suficiente para este proyecto.

## Endpoints

| Método | Path | Rol | HU |
|--------|------|-----|----|
| GET | `/actuator/health` | Público | — |
| GET | `/api/v1/campaigns/pending` | CLIENTE | HU12 |
| GET | `/api/v1/campaigns/{id}` | Autenticado | HU13 |
| PATCH | `/api/v1/campaigns/{id}/status` | CLIENTE, SUPERADMIN | HU14 |

Todos los endpoints `/api/v1/**` requieren `Authorization: Bearer <token>`.
El token es emitido por Django (`POST /api/auth/token/`) y validado aquí.

## Optimistic locking

El campo `version` en cada campaña protege contra escrituras concurrentes entre Django y Spring Boot.
Al hacer `PATCH /{id}/status`, si otra operación ya modificó la campaña, recibirás HTTP 409:

```json
{
  "success": false,
  "message": "La campaña fue modificada por otro proceso. Recarga e intenta de nuevo.",
  "data": null
}
```
# WebSocket seguro para clientes

`/ws/client-campaigns` permite el handshake, pero no entrega campañas hasta
recibir, en los primeros 5 segundos, el mensaje
`{"type":"authenticate","token":"<access JWT>"}`. No pongas tokens en la URL.
El servidor responde `{"type":"authenticated"}` antes de enviar eventos.

Solo admite clientes activos con JWT de acceso firmado, vigente y con la
versión actual de su cuenta. No admite refresh tokens. Los eventos se dirigen
por el correo del dueño de la campaña, obtenido del dominio; nunca por un
destinatario que el navegador elija. Antes de enviar se revalida la cuenta;
las sesiones vencidas o revocadas no reciben datos.

Configura `APP_WEBSOCKET_ALLOWED_ORIGINS` con los orígenes HTTPS exactos de la
web al desplegar. No uses `*`; desarrollo conserva los orígenes locales.
En producción la conexión debe ser WSS. El cierre 1008 indica rechazo de
autenticación/permisos o vencimiento. La web comprueba su sesión HTTP antes de
conectar y reconectar, para renovar el access token cuando corresponde.

**Despliega React y Spring juntos:** este cambio reemplaza el canal anónimo
por autenticación en el primer mensaje. Los clientes antiguos no reciben eventos.
No cambia el contrato REST ni los registros de campañas/usuarios.
