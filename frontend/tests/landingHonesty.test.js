import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')
const flow = read('../src/components/landing/FlowDemo.jsx')
const hero = read('../src/components/landing/HeroSection.jsx')
const pricing = read('../src/components/landing/PricingSection.jsx')
const gallery = read('../src/components/landing/ShowcaseGallery.jsx')
const authPanel = read('../src/components/auth/AuthBrandPanel.jsx')
const login = read('../src/pages/LoginPage.jsx')

test('el flujo de la portada empieza por Dictar, está rotulado y no llama a servicios', () => {
  assert.match(flow, /const STEPS = \['Dictar', 'Generar', 'Aprobar', 'Publicar', 'Medir'\]/)
  assert.match(flow, /Ejemplo de flujo/)
  assert.match(flow, /no usa IA ni publica nada/)
  assert.match(flow, /sin dato/)
  for (const source of [flow, hero]) assert.doesNotMatch(source, /fetch\(|axios|services\/api|socialApi/)
  assert.doesNotMatch(hero, /twitter|tiktok/i)
})

test('los datos inventados se conservan y se rotulan como ejemplo', () => {
  assert.match(pricing, /'S\/ 99'/)
  assert.match(pricing, /'S\/ 299'/)
  assert.match(pricing, /Precio de ejemplo/)
  assert.match(pricing, /Precios y planes de ejemplo/)
  assert.match(flow, /98% completado/)
  assert.match(login, /Generación 10× más rápida/)
  assert.match(login, /demo: true/)
  assert.match(authPanel, /Elena Rodríguez/)
  assert.match(authPanel, /Testimonio de ejemplo, no es un cliente real/)
  assert.match(authPanel, /Dato de ejemplo/)
})

test('la galería es estática y avisa que las imágenes son de ejemplo', () => {
  assert.doesNotMatch(gallery, /useAnimationFrame|repeat: Infinity|drag=/)
  assert.match(gallery, /No son clientes ni publicaciones reales/)
})
