import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8')
const light = css.split('@theme {')[1].split('\n}')[0]
const dark = css.split("html[data-theme='dark'] {")[1].split('\n}')[0]

function color(block, token) {
  const value = block.match(new RegExp(`--color-${token}: (#[a-f0-9]{6});`, 'i'))?.[1]
  assert.ok(value, `falta --color-${token}`)
  return value
}

function luminance(hex) {
  const [r, g, b] = hex.slice(1).match(/../g)
    .map((part) => parseInt(part, 16) / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return r * 0.2126 + g * 0.7152 + b * 0.0722
}

function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

// Texto normal: 4.5:1 (WCAG AA). Cada par es un uso real de la interfaz.
const TEXT_PAIRS = [
  ['on-surface', 'background'],
  ['on-surface', 'surface'],
  ['on-surface-variant', 'background'],
  ['on-surface-variant', 'surface-container-lowest'],
  ['on-surface-variant', 'surface-container-low'],
  ['on-surface-variant', 'surface-container-high'],
  ['primary', 'background'],
  ['primary', 'surface-container-lowest'],
  ['primary', 'surface-container-low'],
  ['on-primary', 'primary'],
  ['on-primary-container', 'primary-container'],
  ['on-primary-fixed', 'primary-fixed'],
  ['primary', 'primary-fixed'], // badge "Pendiente IA"
  ['primary', 'secondary-container'], // badge "Generado"
  ['on-secondary-container', 'secondary-container'],
  ['tertiary', 'warning-container'], // badge "Pendiente aprobación"
  ['on-tertiary-container', 'tertiary-container'], // etiqueta de ejemplo
  ['success', 'success-container'], // badge "Aprobado"
  ['error', 'error-container'], // badge "Rechazado"
  ['error', 'surface-container-lowest'],
  ['success', 'surface-container-lowest'],
  ['outline', 'surface-container-lowest'], // placeholders
]

test('la paleta conserva el marino y el turquesa del icono aprobado', () => {
  assert.equal(color(light, 'navy'), '#14283f')
  assert.equal(color(light, 'turquoise'), '#17b8ad')
  assert.equal(color(light, 'on-surface'), '#14283f')
  assert.equal(color(dark, 'surface'), '#14283f')
  assert.equal(color(dark, 'primary'), '#17b8ad')
  assert.doesNotMatch(css, /#4648d4|#6063ee|#9d76ff|#aeb2ff|#3739bd/i, 'quedan restos del índigo anterior')
})

for (const [name, block] of [['claro', light], ['oscuro', dark]]) {
  test(`texto y estados cumplen AA (4.5:1) en tema ${name}`, () => {
    for (const [fg, bg] of TEXT_PAIRS) {
      const ratio = contrast(color(block, fg), color(block, bg))
      assert.ok(ratio >= 4.5, `${fg} sobre ${bg}: ${ratio.toFixed(2)}:1`)
    }
  })
}

test('el texto sobre el panel marino de marca cumple AA', () => {
  const navy = color(light, 'navy')
  for (const token of ['on-navy', 'on-navy-muted', 'turquoise', 'turquoise-soft']) {
    const ratio = contrast(color(light, token), navy)
    assert.ok(ratio >= 4.5, `${token} sobre navy: ${ratio.toFixed(2)}:1`)
  }
})

test('no vuelven las reglas globales que quitaban bordes y forzaban radio a todo div', () => {
  assert.doesNotMatch(css, /#root :where\(div/)
  assert.doesNotMatch(css, /border-width: 0;/)
  assert.match(css, /--radius-xl: 0\.875rem/)
  assert.match(css, /prefers-reduced-motion: reduce/)
})
