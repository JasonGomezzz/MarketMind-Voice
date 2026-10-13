# Estadísticas de publicaciones — implementación local, 12 de octubre de 2026

Referencia: asesoría de Google Drive del 29 de septiembre, transcripción 4:17–9:38
y fotogramas revisados directamente en 7:48 y 8:52. Dos columnas por plataforma,
totales arriba, gráficos mensuales debajo; detalle por publicación dentro de campaña.
Tras aclaración visual del usuario: totales históricos arriba, dos gráficos de barras
lado a lado por plataforma, meses Ene–Dic en el eje. El selector de año solo cambia
las gráficas; no existe selector de mes. La semántica de las mediciones sigue limitada
como se explica debajo, sin usar cifras simuladas del esquema como datos reales.

## Implementado

- Dashboard y detalle de campaña de marketero: bloques Facebook, Instagram, X y TikTok.
  Google Ads se distingue como anuncios todavía no integrados, sin métricas orgánicas ficticias.
- Solo cuentan publicaciones `published`, incluyendo versiones anteriores. Envíos pendientes
  se muestran aparte. No se infiere publicación TikTok por ver contenido similar en el perfil.
- Gráfico de publicaciones por mes/año, según fecha local de registro del envío confirmado
  (TikTok usa fecha de confirmación cuando existe). No se afirma fecha exacta de publicación remota.
- Últimos contadores acumulados por publicación, cobertura y fecha de medición. Ausencia es null,
  no cero. En Facebook me gusta filtra LIKE, no el total de todas las reacciones.
- Consulta explícita de Meta por propietario y publicación confirmada, GET con token cifrado
  descifrado solo en servidor y enviado por cabecera; sin redirecciones ni publicación.
- Una medición por día y publicación, actualizable; mínimo cinco minutos entre mediciones exitosas.
  Se conservan datos anteriores ante fallos. Reconexion: solo cuenta con mismo propietario y
  mismo identificador inmutable, sin alterar la FK histórica ni usar cuentas de otro usuario.
- Me gusta por mes: suma de los últimos contadores acumulados de las publicaciones
  registradas en cada mes. Funciona desde la primera medición, sin exigir dos meses.
  No representa el mes en que ocurrió cada like: una publicación de enero puede acumular
  nuevos likes posteriormente. Se informa cobertura por mes y no se inventan ceros
  donde faltan mediciones. Los totales históricos siguen independientes del año seleccionado.
- Admin lee agregados; no consulta con credenciales ajenas. API cliente no habilitada;
  el frontend cliente/Spring y móvil necesitan integración posterior con autorización propia.

## Rutas (API principal autenticada, NO bridge público)

- GET `/api/campaigns/publication-statistics/?year=2026`
- GET `/api/campaigns/7/publication-statistics/?year=2026`
- POST `/api/campaigns/7/publication-statistics/refresh/`
  JSON `platform` facebook/instagram y `publication_id` del historial propio.
  Nunca aceptar IDs remotos arbitrarios ni texto/token del navegador.

## Ejecutar y verificar

Desde raíz: `./scripts/backup-postgres.ps1` antes de migrar.
Desde backend: `./venv/Scripts/python.exe manage.py migrate campaigns`
(`0021_publication_metric_snapshot`), luego servidor normal
`./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000`.
Desde frontend: `npm run dev`, abrir localhost:5173/dashboard.
Pruebas: backend `./venv/Scripts/python.exe -m pytest -q`;
frontend `node --test tests/*.test.mjs`, `npm run lint`, `npm run build`.
No se añade scheduler ni sondeo de métricas: usar Consultar métricas tras recibir interacciones.

## Pendiente y resultados reales

La campaña de prueba tiene publicaciones confirmadas en Facebook, Instagram y X;
el envío TikTok sigue inbox. No se republicó ni se cambió contenido/estado de campaña.
La publicación Instagram quedó sin FK de cuenta tras reconectar, pero existe conexión
autorizada coincidente: el lector reconoce esa conexión. Tras confirmar la cuenta de
desarrollador, Instagram permite consultar contadores y guardar una medición real.
Facebook sigue rechazando la lectura con error10, solicitando pages_read_user_content
o Page Public Content Access. No afirmar que todas las plataformas funcionan por mocks.
Revisar permisos/configuración de Meta y probar hasta obtener los contadores restantes.
No modificar OAuth ni conceder permisos adicionales automáticamente.

Vistas y compartidos de Instagram necesitan Insights adicional; lectura de interacciones
X/TikTok no implementada, no se hicieron llamadas pagadas a X. Google Ads, pantallas cliente,
móvil y mediciones programadas pendientes. No habilitar permisos Insights ni revisión de apps
sin revisar requisitos oficiales y autorización del usuario.

Los documentos legales públicos siguen siendo borradores: revisar su coherencia antes de
publicar la funcionalidad. Código y guía locales sin push; Obsidian/backups/.env fuera del repo.
