import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, writeFile, readdir, access } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { prepareLegalSite } from './prepare-legal-site.mjs'

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), 'nexomark-legal-test-'))
  const source = path.join(root, 'source')
  const target = path.join(root, 'output')
  await mkdir(path.join(source, 'historial'), { recursive: true })
  for (const name of ['index.html', 'privacidad.html', 'terminos.html']) {
    await writeFile(path.join(source, name), '<html>BORRADOR <a href="styles.css">Estilo</a></html>')
  }
  await writeFile(path.join(source, 'styles.css'), 'body { color: black }')
  await writeFile(path.join(source, '.env'), 'DO_NOT_DEPLOY')
  await writeFile(path.join(source, 'README.md'), 'Internal instructions')
  await writeFile(path.join(source, 'historial', 'privacidad-v0.1-2026-10-11.html'), '<html>Historial</html>')
  return { source, target }
}

test('draft publication blocked by default without creating output', async () => {
  const input = await fixture()
  await assert.rejects(prepareLegalSite(input), /Publicación bloqueada/)
  await assert.rejects(access(input.target))
})
test('explicit draft preparation copies only the allowed public files', async () => {
  const input = await fixture()
  const result = await prepareLegalSite({ ...input, allowDrafts: true })
  assert.equal(result.drafts, true)
  assert.deepEqual((await readdir(input.target)).sort(), ['.nojekyll', 'historial', 'index.html', 'privacidad.html', 'styles.css', 'terminos.html'])
  await assert.rejects(access(path.join(input.target, '.env')))
  await assert.rejects(access(path.join(input.target, 'README.md')))
})
test('existing output cannot be overwritten', async () => {
  const input = await fixture()
  await mkdir(input.target)
  await assert.rejects(prepareLegalSite({ ...input, allowDrafts: true }), /no se sobrescribe/)
})
test('links to files excluded from deployment fail before creating output', async () => {
  const input = await fixture()
  await writeFile(path.join(input.source, 'index.html'), '<a href="README.md">No publicar</a>')
  await assert.rejects(prepareLegalSite({ ...input, allowDrafts: true }), /fuera del sitio/)
  await assert.rejects(access(input.target))
})
