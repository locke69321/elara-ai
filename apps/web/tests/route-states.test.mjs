import { readFileSync } from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

function read(path) {
  return readFileSync(path, 'utf8')
}

test('execution route includes approval-required interruption panel', () => {
  const source = read(new URL('../src/routes/execution.tsx', import.meta.url))
  assert.match(source, /status="required"/)
  assert.match(source, /ApprovalBanner/)
})

test('execution route includes replay resume controls', () => {
  const source = read(new URL('../src/routes/execution.tsx', import.meta.url))
  assert.match(source, /replay-resume-controls/)
  assert.match(source, /Replay from Sequence/)
})

test('companion route exposes composer and memory transparency chips', () => {
  const source = read(new URL('../src/routes/companion.tsx', import.meta.url))
  assert.match(source, /companion-message-input/)
  assert.match(source, /MemoryHitChip/)
})
