# Facebook: conexión de Páginas por marketero

Esta etapa conecta Páginas; no publica campañas ni modifica Instagram. El botón
de Facebook en una campaña conserva su comportamiento anterior hasta implementar
la publicación con vista previa y confirmación.

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

Prueba real pendiente: autorizar en el navegador y verificar que Aroma Andino aparece
conectada. Los tests automatizados simulan Meta y no realizan publicaciones.

Referencia oficial: [Tokens de Páginas administradas, colección de Meta](https://www.postman.com/meta/facebook/request/bqfxwbp/get-access-tokens-of-pages-you-manage).
