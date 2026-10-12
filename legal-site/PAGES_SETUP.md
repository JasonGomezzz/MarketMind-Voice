# Configurar GitHub Pages para documentos de NexoMark

Estado: incorporación autorizada de estos archivos al repo público en `piero`.
Jason confirmó la fuente GitHub Actions en Pages; el workflow no se ha ejecutado
y no hay URL pública verificada. Subir el código no despliega el sitio.
La aplicación sigue en laptop. Pages no incluye servidor, PostgreSQL, backups ni Obsidian.

## Para Jason

1. Abrir `JasonGomezzz/MarketMind-Voice` con la cuenta que administra el repo.
2. En Settings → Pages → Build and deployment, elegir **GitHub Actions**.
   No seleccionar la raíz de `piero` para publicar todo el proyecto.
3. Revisar el environment `github-pages`: permitir la rama que se publicará y, si lo desean,
   exigir un revisor. No cambiar la rama predeterminada ni conceder administración solo para esto.
4. Habilitar Actions si está desactivado. Estas acciones usan permisos mínimos del token
   temporal de GitHub; no requieren guardar un token personal, contraseña ni claves de proveedores.

## Archivos y rama de ejecución

Se autorizó subir únicamente `legal-site/`, `.github/workflows/legal-pages.yml`
y los dos archivos `scripts/prepare-legal-site*.mjs`. No incluye scripts/backups de PostgreSQL.
El repo de trabajo sigue en `piero`; **GitHub requiere que el workflow manual exista también
en la rama predeterminada** para mostrar Run workflow. El administrador debe incorporar
esos archivos allí mediante un cambio revisado; no fusionar automáticamente todas las diferencias
de `piero`, ni cambiar la rama por defecto para resolverlo. No se ha creado una PR para este paso.
Una vez disponible, seleccionar explícitamente la rama revisada al ejecutar.

## Publicación manual posterior

En Actions → Publicar documentos NexoMark → Run workflow:

- Marcar la confirmación de publicación únicamente con autorización de ambos responsables.
- `allow_drafts` está desmarcado por defecto y bloquea los textos con avisos/pendientes.
  Si autorizan un sitio público de borradores, marcarlo mantiene esos avisos visibles.
  Ese sitio no equivale a políticas vigentes ni debe presentarse como aprobación de TikTok.
- Revisar que el entorno permita esa rama y autorizar el despliegue si existe revisor.
- Esperar éxito y usar la URL exacta emitida por GitHub; no asumir una URL ya activa.

El preparador incluye index, privacidad, términos, estilos e historial HTML con enlaces válidos.
No publica README, CAMBIOS, estas instrucciones ni la raíz del repositorio. Sin embargo,
si estos documentos se suben al repo público, su código e historial serán visibles allí.
Nombres y correo del proyecto serán públicos; no incluye claves ni datos de campañas.

## Después de publicar

Comprobar sin iniciar sesión los enlaces `/privacidad.html` y `/terminos.html` bajo la URL
real del sitio; verificar estilo, versión, enlaces, acceso móvil y avisos de estado.
Las políticas para producción deben estar revisadas y vigentes, sin pendientes sin resolver.
Solo después usar URLs verificadas en TikTok. Pages no reemplaza el sitio funcional ni el
callback HTTPS, y no garantiza revisión o auditoría aprobada de TikTok.

Referencias oficiales:

- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
