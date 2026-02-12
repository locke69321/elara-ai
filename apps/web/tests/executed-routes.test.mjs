import assert from 'node:assert/strict'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'
import test from 'node:test'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'
import typescript from 'typescript'

const routes = [
  { file: 'src/routes/__root.tsx', pathname: '/agent-studio' },
  { file: 'src/routes/companion.tsx', pathname: '/companion' },
  { file: 'src/routes/execution.tsx', pathname: '/execution' },
  { file: 'src/routes/agent-studio.tsx', pathname: '/agent-studio' },
]
const executedRouteReportPath =
  process.env.ELARA_WEB_EXECUTED_ROUTE_REPORT ??
  fileURLToPath(new URL('../coverage/executed-route-modules.json', import.meta.url))

function compileAndExecuteRoute(file, pathname) {
  const fileUrl = new URL(`../${file}`, import.meta.url)
  const absolutePath = fileURLToPath(fileUrl)
  const source = readFileSync(fileUrl, 'utf8')
  const transpiled = typescript.transpileModule(source, {
    compilerOptions: {
      target: typescript.ScriptTarget.ES2022,
      module: typescript.ModuleKind.CommonJS,
      jsx: typescript.JsxEmit.React,
    },
    fileName: absolutePath,
  })

  const invokedComponents = []
  const registerRoute = (routePath) => (definition) => {
    assert.equal(typeof definition.component, 'function')
    invokedComponents.push(definition.component.name || routePath)
    definition.component()
    return { path: routePath, ...definition }
  }
  const requireStub = (specifier) => {
    if (specifier === '@tanstack/react-router') {
      return {
        Outlet: () => null,
        createRootRoute: registerRoute('/'),
        createFileRoute: (routePath) => registerRoute(routePath),
      }
    }
    if (specifier.endsWith('.css')) {
      return {}
    }
    if (specifier.endsWith('components/app-shell')) {
      return { AppShell: () => null }
    }
    if (specifier.endsWith('components/memory-hit-chip')) {
      return { MemoryHitChip: () => null }
    }
    if (specifier.endsWith('components/approval-banner')) {
      return { ApprovalBanner: () => null }
    }
    if (specifier.endsWith('components/timeline-event')) {
      return { TimelineEvent: () => null }
    }
    if (specifier.endsWith('components/specialist-form')) {
      return { SpecialistForm: () => null }
    }
    if (specifier.endsWith('lib/server/dual-mode')) {
      return {
        listSpecialists: () => [],
        postCompanionMessage: () => ({ ok: true }),
        postExecutionGoal: () => ({ ok: true }),
      }
    }
    throw new Error(`Unsupported route import in coverage execution test: ${specifier}`)
  }

  const module = { exports: {} }
  const sandbox = {
    module,
    exports: module.exports,
    require: requireStub,
    React: {
      createElement: () => ({}),
    },
    window: { location: { pathname } },
  }
  sandbox.global = sandbox
  sandbox.globalThis = sandbox

  vm.runInNewContext(transpiled.outputText, sandbox, { filename: absolutePath })
  return { moduleExports: module.exports, invokedComponents }
}

test('route modules execute through route registration', () => {
  const executedFiles = []
  for (const route of routes) {
    const executed = compileAndExecuteRoute(route.file, route.pathname)
    assert.ok(executed.moduleExports.Route)
    assert.ok(executed.invokedComponents.length >= 1)
    executedFiles.push(route.file)
  }

  mkdirSync(dirname(executedRouteReportPath), { recursive: true })
  writeFileSync(
    executedRouteReportPath,
    JSON.stringify({ executedFiles }, null, 2),
    'utf8',
  )
})
