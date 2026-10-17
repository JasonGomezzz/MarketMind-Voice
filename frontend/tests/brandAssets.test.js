import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const read = (path) => readFileSync(new URL(path, import.meta.url))
const PNG = '89504e470d0a1a0a'

function pngSize(buffer) {
  assert.equal(buffer.subarray(0, 8).toString('hex'), PNG)
  return [buffer.readUInt32BE(16), buffer.readUInt32BE(20)]
}

test('el icono aprobado y sus reducciones son PNG del tamaño esperado', () => {
  assert.deepEqual(pngSize(read('../../brand/nexomark-icon-approved-1024.png')), [1024, 1024])
  assert.deepEqual(pngSize(read('../public/nexomark-icon-192.png')), [192, 192])
  assert.deepEqual(pngSize(read('../public/favicon.png')), [64, 64])
})

test('favicon, logo e idioma usan la marca NexoMark', () => {
  const html = read('../index.html').toString()
  const logo = read('../src/components/BrandLogo.jsx').toString()
  assert.match(html, /<html lang="es">/)
  assert.match(html, /<title>NexoMark IA — De la idea dictada al post publicado<\/title>/)
  assert.match(html, /rel="icon" type="image\/png" sizes="64x64" href="\/favicon\.png"/)
  assert.doesNotMatch(html, /favicon\.svg/)
  assert.match(logo, /src="\/nexomark-icon-192\.png"/)
})
