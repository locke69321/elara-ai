import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/companion')({
  component: CompanionPage,
})

function CompanionPage() {
  return (
    <section className="space-y-5">
      <h2 className="text-xl font-medium">Companion</h2>
      <p className="text-sm text-slate-700">
        Maintain conversational continuity while grounding replies with workspace memory.
      </p>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Conversation Timeline
        </h3>
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          <li>Primary companion remembers prior interactions.</li>
          <li>Replies can surface relevant memory hits for transparency.</li>
          <li>Switching modes preserves identity and context.</li>
        </ul>
      </div>

      <form className="rounded-lg border border-slate-200 bg-white p-4">
        <label className="block text-sm font-medium text-slate-800" htmlFor="companion-message">
          Message
        </label>
        <textarea
          id="companion-message"
          className="mt-2 min-h-28 w-full rounded-md border border-slate-300 p-3 text-sm"
          placeholder="Send a message to your companion agent..."
        />
        <button
          type="button"
          className="mt-3 rounded-md bg-slate-900 px-4 py-2 text-sm text-white"
        >
          Send Companion Message
        </button>
      </form>
    </section>
  )
}
