# Documentos públicos de NexoMark — borradores

Estos archivos son borradores para revisión, no políticas vigentes ni un sitio desplegado.
Se autorizó incorporar esta carpeta y el preparador de Pages al repositorio público en `piero`.
Los nombres de los responsables y el correo del proyecto serán visibles en el repositorio.
Jason confirmó la fuente GitHub Actions en Pages. El workflow es manual y bloquea borradores
por defecto; no se ha ejecutado ni completado TikTok. Consultar `PAGES_SETUP.md`.

## Revisar

Abra `index.html` en un navegador y siga los enlaces. No requiere servidor, dependencias ni sesión.
También puede abrir `privacidad.html` y `terminos.html` directamente.

## Antes de publicar

- Los responsables y el correo público ya fueron confirmados por el usuario.
- Revisar datos tratados, accesos, proveedores, ubicaciones y posibles transferencias.
- Definir conservación, copias de seguridad y procedimiento manual para solicitudes.
- Actualizar TikTok solo cuando se verifique la integración implementada.
- Revisar las condiciones de uso y su adecuación legal; retirar los avisos de borrador
  y establecer fecha de vigencia únicamente después de aprobar el texto.

## Versiones

La versión actual es el borrador v0.10, del 11 de octubre de 2026, sin vigencia.
`historial/` conserva v0.1 a v0.9 con enlaces relativos adaptados para poder consultarlas.
Conexión TikTok implementada localmente y probada con mocks, sin credenciales ni OAuth real.
El envío/publicación TikTok sigue pendiente; consultar `../backend/TIKTOK_SETUP.md`.
Ambos responsables atenderán el correo público; se describe un procedimiento manual de solicitudes.
Antes de publicar, comprobar acceso seguro al buzón, registro privado y eliminación de datos/respaldos.
Se añadieron referencias oficiales de proveedores. Confirmar modalidad Gemini, condiciones de
conservación y procesamiento; no declarar una región o garantías de no entrenamiento sin evidencia.
Se revisó el informe DOCX del proyecto y la configuración actual: Gemini para texto,
imagen, transcripción y voz; Django y n8n usan la misma clave (sin exponerla).
El informe no acredita texto gratuito ni facturación actual. La política describe esa incertidumbre
y recomienda datos ficticios para pruebas mientras se verifica la cuenta. No confundir créditos internos
con saldo Google. El DOCX privado no se copia a este sitio ni a un despliegue público.
El usuario confirmó ejecución en laptop por ahora; avisará si decide desplegar la aplicación.
Gemini, redes sociales y el túnel ngrok siguen siendo servicios externos cuando se usan.
Se verificó conexión a PostgreSQL local en Docker y volumen persistente compartido por Django/Spring.
La recuperación de contraseña usa SMTP Gmail configurado. Campañas: n8n local y Resend
confirmado en el workflow publicado/activo (webhook `marketmind-email` dentro del workflow IA).
No se enviaron correos de prueba ni se validó la entrega o la vigencia de credenciales externas.
Se creó un respaldo manual PostgreSQL y se restauró en una base de prueba separada (27 tablas).
Ver `../scripts/POSTGRES_BACKUP.md`. No hay rutina periódica, rotación automática ni copia externa.
Organizar custodia y conservación y revisar procesamiento externo antes de dar vigencia a la política.
La evaluación se prevé en unas nueve semanas desde esa fecha; su fecha exacta y la
continuidad del proyecto están pendientes. No se ha programado un cierre ni un borrado automático.
`CAMBIOS.md` registra los cambios. La rotación de backups de 30 días es una propuesta,
no un mecanismo implementado; revisión al cierre de tesis y atención manual requieren ejecución.
Ningún cambio documental crea funciones de borrado, respaldos ni integración TikTok.

## Publicación futura en GitHub Pages

Con autorización, subir solamente estos archivos estáticos y configurar una fuente de Pages
adecuada (rama dedicada o un workflow que despliegue exclusivamente esta carpeta).
No publicar la raíz del proyecto, `.env`, credenciales, bases de datos ni campañas de usuarios.
El repositorio se mantiene en la rama de trabajo actual; este borrador no cambia ramas ni ajustes.

Las URLs de privacidad y términos deben comprobarse en el sitio desplegado antes de usarse
en TikTok. La fuente GitHub Actions está seleccionada, pero no hay URL pública verificada.

GitHub Pages puede alojar estos documentos, pero este índice informativo no sustituye
el sitio funcional requerido para revisar una aplicación web en TikTok.

Referencias:

- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://developers.tiktok.com/docs/en/app-review-guidelines
