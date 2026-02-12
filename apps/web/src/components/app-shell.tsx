import { ModeTabs } from './mode-tabs'

type Mode = 'companion' | 'execution' | 'agent-studio'

export function AppShell(props: {
  activeMode: Mode
  workspaceName: string
  connectionStatus: 'online' | 'offline'
  children?: unknown
}) {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <p className="brand-kicker">Field Console</p>
          <h1>Elara Dual Mode v0.1</h1>
        </div>
        <div className="workspace-panel">
          <p className="workspace-name">{props.workspaceName}</p>
          <span className={`runtime-status ${props.connectionStatus}`}>
            {props.connectionStatus}
          </span>
        </div>
      </header>
      <ModeTabs activeMode={props.activeMode} />
      <section className="route-canvas">{props.children}</section>
    </main>
  )
}
