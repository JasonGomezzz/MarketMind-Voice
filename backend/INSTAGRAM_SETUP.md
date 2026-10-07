# Instagram — conexión por marketero (primera etapa)

Esta etapa permite conectar varias cuentas mediante Instagram Login, listar solo
las del usuario actual y desconectarlas localmente. **No publica campañas todavía**.
No se utiliza un token global de la cuenta de prueba.

## Configuración pendiente

En `backend/.env`, completar `INSTAGRAM_APP_ID` y `INSTAGRAM_APP_SECRET` con los
valores de la **aplicación de Instagram** que muestra Meta (no los de Facebook).
Guardar una clave Fernet independiente en `SOCIAL_TOKEN_ENCRYPTION_KEY`.
Generarla localmente con:

```powershell
venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

No compartir esa salida, no subir `.env` a Git y conservar la clave con las copias
de seguridad: perderla impide descifrar las conexiones guardadas.

`INSTAGRAM_REDIRECT_URI` debe apuntar a `https://<frontend>/settings` y coincidir
exactamente con la URI registrada en el inicio de sesión empresarial de Instagram.
`INSTAGRAM_FRONTEND_ORIGIN` debe tener ese mismo origen HTTPS (si está vacío,
se utiliza `FRONTEND_BASE_URL`). El marketero debe iniciar
sesión desde ese origen, no desde otro dominio/puerto, para conservar su sesión al
volver de Meta. En local, falta definir ese acceso HTTPS y configurar CORS y hosts
de forma explícita; no se crean túneles ni se expone Django automáticamente.

Para no cambiar el origen de los correos de recuperación, usar el origen dedicado
`INSTAGRAM_FRONTEND_ORIGIN` durante la prueba. El perfil `core.settings.instagram_preview`
deshabilita debug y solo expone login, perfil y conexiones de Instagram; no incluye
admin ni campañas. Se ejecuta en 127.0.0.1:8002. La vista Vite opt-in usa
`INSTAGRAM_PREVIEW_HOST` con el dominio exacto y el puerto 5176; debe compilarse con
`VITE_API_URL=/`, `VITE_INSTAGRAM_PREVIEW=true` y salida `dist-instagram`.
El login de esa compilación lleva directamente a Configuración. No es un despliegue de producción.
El resto del proyecto sigue en sus puertos habituales.

Mientras falte configuración, la interfaz muestra el motivo y bloquea conectar.
No rellenar estas variables con el token generado manualmente: el flujo obtiene
un token distinto por autorización. Reiniciar Django después de configurar.

## Seguridad y límites

- Inicio y finalización requieren JWT y rol marketero. El estado de autorización
  se almacena como hash, expira a los diez minutos, está vinculado al usuario y su
  versión de sesión, y se consume atómicamente una sola vez.
- Las credenciales se cifran con Fernet y no aparecen en respuestas ni mensajes de
  error. Solo se solicitan acceso básico y publicación de contenido.
- La interfaz muestra vencimiento; por ahora se requiere reconectar cuando expire.
- Desconectar borra la credencial local, no revoca por sí mismo el permiso en Meta.
- Pruebas de HTTP usan respuestas simuladas; todavía falta validar la autorización
  real con la app y cuenta tester. Meta puede cambiar detalles del contrato.
- Para empresas externas sigue pendiente revisión de permisos/acceso por Meta.
- El siguiente paso será selección de cuenta, vista previa y publicación de una
  campaña aprobada con control de propiedad y prevención de duplicados.

Referencia: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login/
