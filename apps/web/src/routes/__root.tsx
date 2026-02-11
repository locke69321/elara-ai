import { Outlet, createRootRoute } from '@tanstack/react-router'

import { AppShell } from '../components/app-shell'
import '../styles/tokens.css'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  const pathname = typeof window === 'undefined' ? '/companion' : window.location.pathname
  const activeMode =
    pathname.startsWith('/execution')
      ? 'execution'
      : pathname.startsWith('/agent-studio')
        ? 'agent-studio'
        : 'companion'

  return (
    <AppShell
      activeMode={activeMode}
      workspaceName="Workspace: local-workspace"
      connectionStatus="online"
    >
      <Outlet />
    </AppShell>
  )
}
