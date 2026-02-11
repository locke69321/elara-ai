import { Link } from '@tanstack/react-router'

type Mode = 'companion' | 'execution' | 'agent-studio'

const MODES: Array<{ id: Mode; label: string; to: string }> = [
  { id: 'companion', label: 'Companion', to: '/companion' },
  { id: 'execution', label: 'Execution', to: '/execution' },
  { id: 'agent-studio', label: 'Agent Studio', to: '/agent-studio' },
]

export function ModeTabs(props: { activeMode: Mode }) {
  return (
    <nav aria-label="Mode switcher" className="mode-tabs">
      {MODES.map((mode) => (
        <Link
          key={mode.id}
          to={mode.to}
          className={`mode-tab ${props.activeMode === mode.id ? 'is-active' : ''}`}
        >
          {mode.label}
        </Link>
      ))}
    </nav>
  )
}
