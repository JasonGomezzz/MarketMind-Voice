# Conexión de X

En la app de X, configura permisos **Leer y escribir** y tipo **Aplicación Web, Aplicación Automatizada o Bot**. Registra exactamente la URL HTTPS de retorno:

`https://handpick-ungreased-ocelot.ngrok-free.dev/api/auth/x/callback/`

En `backend/.env`, añade las credenciales de OAuth 2.0 mostradas tras guardar la configuración de autenticación:

```dotenv
X_CLIENT_ID=...
X_CLIENT_SECRET=...
X_REDIRECT_URI=https://handpick-ungreased-ocelot.ngrok-free.dev/api/auth/x/callback/
```

No uses Consumer Key, Access Token ni Bearer Token. Conserva `SOCIAL_TOKEN_ENCRYPTION_KEY` existente. Reinicia el Django local (puerto 8000) y el puente HTTPS de pruebas (puerto 8002), que se ejecuta sin recarga automática. Mantén el túnel ngrok apuntando al frontend de pruebas en el puerto 5176.

El marketero pulsa **Conectar X** desde `http://localhost:5173/settings`, autoriza en X y vuelve a localhost. La conexión queda ligada a su usuario y los tokens se guardan cifrados. La autorización se renueva al publicar cuando el token ha vencido.

En una campaña aprobada con Twitter / X seleccionado, **Preparar para Twitter / X** muestra la imagen y el texto completo. El texto se valida con las reglas de X (280 caracteres ponderados, URLs y emojis incluidos); no se recorta. El marketero elige su cuenta y confirma la publicación real. Se sube el JPEG aprobado a `/2/media/upload` y luego se envía a `/2/tweets` con el texto aprobado y el identificador de imagen. Una respuesta ambigua al crear el post bloquea otro envío; los rechazos confirmados permiten volver a confirmar después de resolver el problema. La misma campaña, versión y cuenta no se publica dos veces, incluso si se desconecta y vuelve a conectar.

El acceso de X a la API es de pago por uso: con saldo cero puede fallar incluso la consulta de identidad requerida para finalizar la conexión. La publicación usa la API de X directamente; no necesita exponer una URL pública de imagen en el túnel.
