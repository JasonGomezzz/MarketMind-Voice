# TikTok conexión local — primera etapa

Implementado: conectar cuenta, guardar access/refresh cifrados por propietario, listar y
desconectar localmente, renovación bajo bloqueo y retorno HTTPS a la web local.
Implementado localmente: envío PHOTO/MEDIA_UPLOAD de campañas aprobadas con confirmación,
imagen y texto inmutables, protección de duplicados y confirmación por consulta/webhooks.
El flujo Sandbox tiene pruebas reales de conexión, verificación de medios y envío.
La confirmación posterior de publicación sigue pendiente en el intento de prueba.
Direct Post no implementado.
No requiere cuenta TikTok empresarial
por este flujo de Login Kit, pero sí permisos, cuenta de prueba y configuración válida del Sandbox.

## Configurar después de revisar el portal

En el `.env` privado de backend, sin subirlo a Git:

```dotenv
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_REDIRECT_URI=https://TU-DOMINIO.ngrok-free.dev/api/auth/tiktok/callback/
```

Usar Client key/secret del **mismo Sandbox** que autoriza al Target User.
Conservar `SOCIAL_TOKEN_ENCRYPTION_KEY`; no regenerarla para este cambio.
El portal debe incluir Login Kit Web, redirect URI exacta y Content Posting API con
`user.info.basic` y `video.upload`. No se solicita `video.publish` ni estadísticas/perfil ampliado.
Se muestra display_name, no @username, porque el permiso básico no incluye username.

Aplicar migración `authentication/0010_tiktok_connection` (nuevas tablas, sin borrar datos),
reiniciar backend principal y puente si usan `--noreload`, y recompilar preview HTTPS.
No cambiar ni habilitar credenciales de producción mientras se prueba Sandbox.
Frontend: Configuración → TikTok → Conectar; autorizar en TikTok y volver a Configuración.
Sin credenciales/retorno HTTPS válidos, el panel deja el botón deshabilitado.

El callback público solo retransmite código/estado al fragmento del origen permitido.
El navegador valida su estado temporal y lo borra de la URL; solo después el backend
autenticado del propietario canjea y consume la autorización una vez. Código, tokens y secret
no se muestran en la lista de cuentas ni en errores. El puente no expone endpoints de campañas.
Evitar copiar URLs OAuth con códigos; la redacción de logs cubre el nuevo callback.

Desconectar elimina la conexión local y cancela autorizaciones pendientes de ese usuario;
no elimina publicaciones ni revoca automáticamente el permiso en TikTok. Revocarlo allí si se desea.
El envío Sandbox fue probado; no se ha certificado revisión/auditoría de TikTok.

## Envío de imagen: requisitos de configuración

Aplicar `campaigns/0019_tiktok_upload` después de un respaldo local. No hay borrado de datos.
El bridge sirve únicamente `/api/tiktok/media/<ticket>/`: JPEG de la campaña confirmada,
ticket aleatorio de una hora y sin caché. No se exponen endpoints de envío ni campañas en el bridge.
No usar GitHub Pages para subir imágenes privadas de campañas.

Configurar privadamente `TIKTOK_MEDIA_BASE_URL=https://TU-DOMINIO/api/tiktok/media/`.
Verificar ese prefijo o su dominio en TikTok → URL properties / Content Posting API → Verify.
Seguir el método y archivo exactos que proporcione el portal; no inventar la firma.
Para el método signature file, descargar el .txt del portal y configurar privadamente
`TIKTOK_VERIFICATION_FILE` con su ruta absoluta. El bridge sirve solo ese nombre exacto
bajo `/api/tiktok/media/`, sin barra final y sin exponer el directorio ni otros archivos.
El archivo no se copia al repo. Reiniciar el bridge si usa --noreload.
La firma es un archivo público de prueba de propiedad, no el Client secret.
ngrok gratuito puede mostrar su aviso a navegadores; comprobar respuesta sin redirección
con un cliente no navegador y luego el Verify real del portal. Una comprobación local
no sustituye el resultado de verificación de TikTok.
Solo después de comprobar la verificación activar `TIKTOK_MEDIA_VERIFIED=true`.
El valor por defecto es false y bloquea todos los envíos. No activarlo para saltar requisitos.

Campaña aprobada → Preparar para TikTok → elegir cuenta → revisar imagen/texto → confirmar.
No se recorta ni reescribe texto automáticamente: máximo 4000 unidades UTF-16.
Se marca `is_aigc=true`. En TikTok el usuario termina edición y revisa etiquetas comerciales/IA.
Consultar estado no reenvía; espera mínima 30 segundos entre consultas reales por intento.
Estados: processing (no publicado), inbox (notificación, no publicado), published (confirmación
de TikTok), failed o uncertain (sin reenvío automático). Si la solicitud inicial es ambigua,
revisar TikTok; no se crea otro intento para esa cuenta/versión.
Las pruebas automatizadas utilizan mocks. Durante la implementación inicial no se
realizaron envíos reales; el usuario envió/publicó después la campaña 7, descrita abajo.

## Confirmación automática (12 de octubre de 2026)

Implementado localmente: callback HTTPS `/api/tiktok/webhook/` en servidor principal
y bridge restringido. Configurar en el portal TikTok la URL completa del webhook
del mismo Sandbox/client key (NO sustituir el redirect OAuth).
Ejemplo: `https://TU-DOMINIO.ngrok-free.dev/api/tiktok/webhook/`.
Mantener el backend/bridge/preview/túnel activos para recibir eventos.

El receptor valida HMAC-SHA256 del cuerpo original con Client secret y timestamp
de hasta cinco minutos; coteja client key, user_openid y publish_id del intento
guardado. Solo `post.publish.complete` o `post.publish.publicly_available`
confirman publicación. Eventos repetidos son idempotentes y eventos atrasados
de inbox/fallo no degradan una publicación confirmada. No se infiere éxito a partir
de un texto/imagen parecidos ni se aceptan marcas manuales. No se guardan cuerpos
de eventos ni credenciales en los recibos de deduplicación.

El modal consulta el estado cada 30 segundos mientras esté abierto y detiene
el sondeo en published/failed. Esto consulta, nunca reenvía. El resumen de destinos
incluye el estado TikTok para la versión actual.

Aplicar migración `campaigns/0020_tiktok_confirmation` después de respaldo;
reiniciar el bridge si está iniciado con --noreload. El GET público es únicamente
un diagnóstico de routing, no prueba recepción real de un evento firmado.

Estado conocido en la prueba local: campaña enviada por el usuario; la foto con
música aparece en su perfil, pero status/fetch continúa SEND_TO_USER_INBOX.
La implementación del webhook NO demuestra que TikTok haya confirmado esa foto,
ni garantiza reenvío retroactivo de eventos anteriores. Webhooks añadido y URL
guardada en el Sandbox el 12 de octubre; persistencia comprobada al recargar.
El evento oficial de prueba `tiktok.ping` devolvió 200 OK desde el portal.
Esto prueba entrega del diagnóstico, NO confirmación de publicación: aún falta
un evento de publicación real o PUBLISH_COMPLETE. No reenviar esa campaña para probarlo.

Referencias: https://developers.tiktok.com/docs/en/webhooks-verification y
https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status.

Referencias verificadas:

- https://developers.tiktok.com/docs/en/login-kit-web
- https://developers.tiktok.com/docs/en/oauth-user-access-token-management
- https://developers.tiktok.com/docs/en/tiktok-api-v2-get-user-info
