import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

function read(path) {
  return readFileSync(path, 'utf8')
}

test('root route exposes dual-mode navigation links', () => {
  const source = read(new URL('../src/routes/__root.tsx', import.meta.url))
  assert.match(source, /Companion/)
  assert.match(source, /Execution/)
  assert.match(source, /Agent Studio/)
})

test('server boundary function is defined with createServerFn', () => {
  const source = read(new URL('../src/lib/server/get-workspace.ts', import.meta.url))
  assert.match(source, /createServerFn/)
  assert.match(source, /method: 'GET'/)
})

test('core routes are present', () => {
  const companion = read(new URL('../src/routes/companion.tsx', import.meta.url))
  const execution = read(new URL('../src/routes/execution.tsx', import.meta.url))
  const studio = read(new URL('../src/routes/agent-studio.tsx', import.meta.url))

  assert.match(companion, /createFileRoute\('\/companion'\)/)
  assert.match(execution, /createFileRoute\('\/execution'\)/)
  assert.match(studio, /createFileRoute\('\/agent-studio'\)/)
  assert.match(companion, /Send Companion Message/)
  assert.match(execution, /Execute Goal/)
  assert.match(studio, /Save Specialist Agent/)
})
