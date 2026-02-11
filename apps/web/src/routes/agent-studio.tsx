import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/agent-studio')({
  component: AgentStudioPage,
})

function AgentStudioPage() {
  return (
    <section>
      <h2 className="text-xl font-medium">Agent Studio</h2>
      <p className="mt-3 text-sm text-slate-700">
        Configure specialist prompts, soul metadata, and capabilities.
      </p>
    </section>
  )
}
