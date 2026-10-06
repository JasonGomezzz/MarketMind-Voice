---
version: 1
slug: "src-pages-publicationsstatspage-jsx"
primary_target: "src/pages/PublicationsStatsPage.jsx"
related_targets: []
---

# Estadísticas de publicaciones

Modo: Operate. Ruta `/stats`, visible para cliente, marketero y superadmin con el mismo componente; el backend recorta los datos por rol.

## Direction contract

THESIS: Cada número nace de una versión aprobada. La página une "lo que el cliente aprobó" con "lo que rindió en la red", en vez del tablero genérico de KPIs sueltos.

OWN-WORLD: Lumina Creative sin cambios: fondo lila claro, tarjetas blancas glass, acento índigo, Inter, cifras tabulares. Los logos reales de Instagram y Facebook son el único color de marca ajeno.

STORY: El visitante ve primero cuánto rinde cada red, después qué publicación lo produjo, y abre una para ver su cadena aprobada → publicada → métricas y actualizarla desde Meta.

FIRST VIEWPORT: Título y alcance del rol con la línea de estado (publicadas · esperando aprobación · fallidas) y "Actualizar métricas" a la derecha; debajo dos paneles por red con logo grande, me gusta / comentarios / compartidos grandes, alcance-vistas-guardados en línea y barras por mes; luego la tabla filtrable.

FORM: estructura 1 de 5 (paneles por red + historial + panel lateral). Sin seed: Jason pidió construir con el diseño actual y revisarlo después.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
