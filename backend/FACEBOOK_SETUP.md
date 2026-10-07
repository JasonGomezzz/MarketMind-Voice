# Facebook: conexión de Páginas por marketero

Conecta Páginas por marketero y publica imagen con texto aprobado mediante una
confirmación explícita dentro de NexoMark. Instagram conserva su flujo propio.

## Meta y entorno local

Usar la aplicación principal de Meta, no el ID/secret del producto Instagram.
Añadir el caso de uso de Páginas y los permisos `pages_show_list`,
`pages_read_engagement`, `pages_manage_posts`. No hace falta `read_insights` en esta etapa.
Registrar exactamente la URL HTTPS `/api/auth/facebook/callback/` en las URI válidas.

Variables privadas de `backend/.env`:

```env
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_REDIRECT_URI=https://TU-DOMINIO.ngrok-free.dev/api/auth/facebook/callback/
FACEBOOK_GRAPH_VERSION=v23.0
# Opcional: configuración de Facebook Login for Business con token de usuario
FACEBOOK_LOGIN_CONFIG_ID=
```

Se reutilizan `FRONTEND_BASE_URL=http://localhost:5173` y la clave Fernet
`SOCIAL_TOKEN_ENCRYPTION_KEY`. Nunca cambiar esa clave mientras haya conexiones
guardadas ni compartir secretos/tokens o subir `.env` al repositorio.
Si Meta exige una configuración de Login for Business, crearla con token de
usuario y los tres permisos anteriores y guardar su ID en `FACEBOOK_LOGIN_CONFIG_ID`.

Aplicar migraciones y reiniciar el puente Django 8002 después de editar entorno.
El túnel existente hacia Vite preview 5176 ya reenvía `/api/` al puente, que añade
únicamente los endpoints de Facebook; no expone campañas ni admin. Recompilar
el preview si se usa su interfaz HTTPS. El usuario trabaja desde localhost.

## Flujo y comprobación

En Configuración → Facebook, pulsar Conectar Facebook. Iniciar sesión con el
perfil que administra Aroma Andino y autorizar esa Página. Con aplicación sin
publicar, usar cuentas con rol permitido en la app; acceso externo queda sujeto
a revisión y requisitos de Meta.

El callback HTTPS valida el estado y devuelve a la pestaña de origen configurada,
con código en fragmento (sin JWT ni tokens de Meta). La sesión local autentica la
finalización y consume una autorización de diez minutos una sola vez. Los estados
de Instagram y Facebook se guardan separados y no procesan callbacks ajenos.

El backend intercambia/amplía el token de usuario, verifica identidad y permisos,
consulta `/me/accounts` y guarda solo Páginas con tarea CREATE_CONTENT o MANAGE.
Guarda los tokens de Página cifrados por propietario, nunca los devuelve al frontend.
La fecha conservadora de renovación se basa en la autorización de usuario, aunque
Meta pueda emitir tokens de Página de mayor duración. No se almacena su token de usuario.
No se siguen URLs arbitrarias de paginación; se usa cursor en el host fijo de Meta.

La lista y desconexión están limitadas al marketero autenticado. Desconectar borra
la credencial local, no revoca automáticamente los permisos en Meta. Eliminar o
reducir permisos en Meta puede invalidar antes una credencial; reconectar entonces.

## Publicación de campañas aprobadas

En localhost, abrir una campaña aprobada con Facebook seleccionado, pulsar
Preparar para Facebook y revisar la imagen, el texto guardado y la Página de
destino. Solo el botón final Publicar hace un POST externo real. La conexión
exitosa de Aroma Andino fue confirmada por el usuario; la prueba de publicación
real queda pendiente de su confirmación en la interfaz. Los tests simulan Meta.

`POST /api/campaigns/<id>/publish-facebook/` exige JWT de marketero, propiedad
de campaña y Página, aprobación, plataforma y versión actuales, `confirm: true`,
texto e imagen válidos y credencial vigente. No admite copy/imagen de un borrador
en el request: toma una instantánea de la campaña guardada. El JPEG se envía por
multipart directamente a `/{page_id}/photos`, con `caption` y `published=true`.
No se necesita que Facebook descargue una imagen desde el túnel.
Límites conservadores de esta integración: texto de 60000 caracteres, JPEG de
4 MB, 20 millones de píxeles de entrada; se reduce sin recortar a 1800×1800.

Se persiste un intento `publishing` antes de la solicitud externa. La restricción
única campaña/Página/versión sobrevive a desconectar y reconectar la Página. Un
doble clic o reintento solo devuelve ese intento. Éxito almacena photo_id y, cuando
Meta lo devuelve, post_id; el frontend ofrece un enlace a la foto en Facebook.
Una respuesta ambigua, timeout o error se marca `uncertain` y no se reenvía:
revisar primero la Página y permisos; no borrar el registro para volver a probar.
Un proceso que muere con estado publishing también requiere revisión manual.
Esto prioriza evitar duplicados, sin prometer exactamente-una-vez en Meta.
GET del mismo endpoint con page_id consulta el estado sin publicar. Los endpoints
de campaña/publicación siguen excluidos del puente público. Desconectar no borra
el historial de publicación ni elimina publicaciones en Facebook.

Referencia oficial: [Tokens de Páginas administradas, colección de Meta](https://www.postman.com/meta/facebook/request/bqfxwbp/get-access-tokens-of-pages-you-manage).
Parámetros de fotos: [SDK oficial de Meta, Page.create_photo](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/page.py).
