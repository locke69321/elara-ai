import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/execution')({
  component: ExecutionPage,
})

function ExecutionPage() {
  return (
    <section className="space-y-5">
      <h2 className="text-xl font-medium">Execution</h2>
      <p className="text-sm text-slate-700">
        Plan goals, delegate subtasks to specialists, and inspect deterministic run events.
      </p>

      <form className="rounded-lg border border-slate-200 bg-white p-4">
        <label className="block text-sm font-medium text-slate-800" htmlFor="goal-input">
          Goal
        </label>
        <input
          id="goal-input"
          type="text"
          className="mt-2 w-full rounded-md border border-slate-300 p-3 text-sm"
          placeholder="Describe what you want executed..."
        />
        <button
          type="button"
          className="mt-3 rounded-md bg-slate-900 px-4 py-2 text-sm text-white"
        >
          Execute Goal
        </button>
      </form>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Delegation Timeline
        </h3>
        <ol className="mt-3 list-decimal space-y-2 pl-6 text-sm text-slate-700">
          <li>run.started</li>
          <li>task.delegated</li>
          <li>task.completed</li>
          <li>run.completed</li>
        </ol>
      </div>
    </section>
  )
}
