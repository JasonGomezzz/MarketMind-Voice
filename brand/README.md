# Identidad de NexoMark IA

Icono aprobado: `nexomark-icon-approved-1024.png` (maestro de 1024 × 1024, traído
de la rama `piero`). Una **N** formada por dos piezas que encajan, una blanca y
otra turquesa, sobre un cuadrado redondeado azul marino: quien crea la campaña y
el cliente que la aprueba. Usar el archivo tal cual, sin redibujar el encaje ni
cambiar sus colores.

## Colores del icono

| Uso | Color |
|---|---|
| Fondo del icono | Azul marino `#14283F` |
| Pieza izquierda | Blanco `#FFFFFF` |
| Pieza derecha | Turquesa `#17B8AD` |

La interfaz web deriva su paleta de estos tres colores (`frontend/src/index.css`,
descrita en `frontend/DESIGN.md`). En modo claro, enlaces y botones con texto
blanco usan turquesa oscuro `#087B75` por contraste; en oscuro, el turquesa
original lleva texto marino. El contraste lo comprueba
`frontend/tests/brandPalette.test.js`.

## Copias en la web

- `frontend/public/nexomark-icon-192.png`: logo de la interfaz (`BrandLogo`) e
  icono para pantallas de inicio.
- `frontend/public/favicon.png`: favicon de 64 × 64.

Ambas son reducciones del maestro (Pillow, Lanczos), sin otros cambios.

No deformar el icono ni separar la cápsula `IA` del nombre. El icono solo puede ir
sin el nombre cuando el nombre ya se ve en el mismo contexto.
