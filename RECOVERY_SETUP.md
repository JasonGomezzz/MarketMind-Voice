# Recuperación de contraseña por correo

En el login, «¿Olvidaste tu contraseña?» abre el formulario de recuperación.
El usuario recibe un enlace de un solo uso con vigencia de 30 minutos.
El cambio invalida los JWT anteriores, incluidos los refresh tokens.

La configuración predeterminada muestra el correo en la terminal de Django
para probar el flujo local. No entrega correos hasta configurar SMTP.

Configura `backend/.env` (archivo privado, nunca subirlo al repositorio):

```dotenv
FRONTEND_BASE_URL=http://localhost:5173
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=servidor-smtp-del-proveedor
EMAIL_PORT=587
EMAIL_HOST_USER=correo-del-proyecto@example.com
EMAIL_HOST_PASSWORD=credencial-smtp-o-contrasena-de-aplicacion
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=NexoMark IA <correo-del-proyecto@example.com>
```

Reinicia Django después de cambiar el archivo. Usa la credencial específica
de SMTP o una contraseña de aplicación; no la contraseña personal del correo.
El proveedor debe permitir enviar desde la dirección configurada.
En producción, `FRONTEND_BASE_URL` debe ser la URL pública HTTPS de la web.

Datos pendientes: proveedor de correo, dirección remitente, servidor y puerto,
método de autenticación y credencial SMTP. Las credenciales deben introducirse
directamente en el `.env`, no en documentos ni commits.
