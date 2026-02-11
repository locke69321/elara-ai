import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

function runCoverageGate(testFiles) {
  return spawnSync(process.execPath, ['./scripts/coverage_gate.mjs'], {
    cwd: fileURLToPath(new URL('..', import.meta.url)),
    env: {
      ...process.env,
      ELARA_WEB_COVERAGE_TESTS: testFiles.join(','),
      ELARA_WEB_COVERAGE_THRESHOLD: '90',
    },
    encoding: 'utf8',
  })
}

test('coverage gate fails when route modules are not executed', () => {
  const run = runCoverageGate(['tests/structure.test.mjs', 'tests/route-states.test.mjs'])
  assert.notEqual(run.status, 0)
  assert.match(`${run.stdout}\n${run.stderr}`, /web coverage gate failed/i)
})

test('coverage gate passes when route modules are executed', () => {
  const run = runCoverageGate([
    'tests/structure.test.mjs',
    'tests/route-states.test.mjs',
    'tests/executed-routes.test.mjs',
  ])
  assert.equal(run.status, 0, `coverage gate output:\n${run.stdout}\n${run.stderr}`)
})
