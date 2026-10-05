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

## Gmail del proyecto

Para las pruebas locales con Gmail, activa la verificación en dos pasos y crea
una contraseña de aplicación para Django. No uses la contraseña normal del correo.
Si Google no permite crear contraseñas de aplicación en esa cuenta, hay que
configurar OAuth o elegir un proveedor de correo transaccional.

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=correo-del-proyecto@gmail.com
EMAIL_HOST_PASSWORD=contrasena-de-aplicacion-sin-espacios
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=NexoMark IA <correo-del-proyecto@gmail.com>
```

Pendiente: confirmar la dirección Gmail del proyecto y que esté habilitada la
verificación en dos pasos. Introduce la contraseña de aplicación directamente
en `backend/.env`, no en el chat, documentos ni commits. Reinicia Django y prueba
«¿Olvidaste tu contraseña?» con una cuenta existente antes de dar por validada
la entrega real del correo.

Referencias oficiales: [contraseñas de aplicación](https://support.google.com/accounts/answer/185833?hl=es)
y [envío SMTP de Google](https://support.google.com/a/answer/176600?hl=es).
