import { spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const threshold = Number.parseInt(process.env.ELARA_WEB_COVERAGE_THRESHOLD ?? '90', 10)

const requiredExecutedFiles = [
  'src/routes/__root.tsx',
  'src/routes/companion.tsx',
  'src/routes/execution.tsx',
  'src/routes/agent-studio.tsx',
]

const defaultTests = [
  'tests/structure.test.mjs',
  'tests/route-states.test.mjs',
  'tests/executed-routes.test.mjs',
]
const testFiles = (process.env.ELARA_WEB_COVERAGE_TESTS ?? defaultTests.join(','))
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean)

if (testFiles.length === 0) {
  throw new Error('web coverage gate requires at least one test file')
}

const executedRouteReportPath = fileURLToPath(
  new URL(`../coverage/executed-route-modules-${process.pid}-${Date.now()}.json`, import.meta.url),
)
rmSync(executedRouteReportPath, { force: true })

const coverageArgs = [
  '--experimental-test-coverage',
  `--test-coverage-lines=${threshold}`,
  ...requiredExecutedFiles.map((file) => `--test-coverage-include=${file}`),
  '--test',
  ...testFiles,
]
const childEnv = {
  ...process.env,
  ELARA_WEB_EXECUTED_ROUTE_REPORT: executedRouteReportPath,
}
for (const envKey of Object.keys(childEnv)) {
  if (envKey.startsWith('NODE_TEST_')) {
    delete childEnv[envKey]
  }
}

const run = spawnSync(process.execPath, coverageArgs, {
  cwd: fileURLToPath(new URL('..', import.meta.url)),
  env: childEnv,
  encoding: 'utf8',
})

if (run.stdout) {
  process.stdout.write(run.stdout)
}
if (run.stderr) {
  process.stderr.write(run.stderr)
}

let executedFiles = []
try {
  const executedFileReport = readFileSync(executedRouteReportPath, 'utf8')
  const parsed = JSON.parse(executedFileReport)
  if (Array.isArray(parsed.executedFiles)) {
    executedFiles = parsed.executedFiles.filter((item) => typeof item === 'string')
  }
} catch {
  executedFiles = []
}
rmSync(executedRouteReportPath, { force: true })

const coveredCount = requiredExecutedFiles.filter((file) => executedFiles.includes(file)).length
const percent = Math.round((coveredCount / requiredExecutedFiles.length) * 100)

const report = {
  threshold,
  executedFileCoverage: requiredExecutedFiles,
  nonExecutableArtifacts: ['src/styles/tokens.css'],
  testFiles,
  percent,
  coveredCount,
  totalFiles: requiredExecutedFiles.length,
  executedFiles,
  exitCode: run.status,
}
mkdirSync(new URL('../coverage/', import.meta.url), { recursive: true })
writeFileSync(
  new URL('../coverage/web-coverage.json', import.meta.url),
  JSON.stringify(report, null, 2),
  'utf8',
)

console.log(`web coverage gate: ${percent}% (${coveredCount}/${requiredExecutedFiles.length})`)

if (run.status !== 0 || percent < threshold) {
  throw new Error('web coverage gate failed: executed route coverage is below threshold')
}
