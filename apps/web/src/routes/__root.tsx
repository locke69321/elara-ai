import { Link, Outlet, createRootRoute } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl p-6">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Elara Dual-Mode Shell</h1>
        <nav className="flex gap-4 text-sm">
          <Link to="/companion" className="underline">
            Companion
          </Link>
          <Link to="/execution" className="underline">
            Execution
          </Link>
          <Link to="/agent-studio" className="underline">
            Agent Studio
          </Link>
        </nav>
      </header>
      <Outlet />
    </main>
  )
}
