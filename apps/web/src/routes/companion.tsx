import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/companion')({
  component: CompanionPage,
})

function CompanionPage() {
  return (
    <section>
      <h2 className="text-xl font-medium">Companion</h2>
      <p className="mt-3 text-sm text-slate-700">
        Conversational and roleplay continuity view.
      </p>
    </section>
  )
}
