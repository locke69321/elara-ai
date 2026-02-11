import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/agent-studio')({
  component: AgentStudioPage,
})

function AgentStudioPage() {
  return (
    <section className="space-y-5">
      <h2 className="text-xl font-medium">Agent Studio</h2>
      <p className="text-sm text-slate-700">
        Configure specialist prompts, soul metadata, and capability scopes for delegation.
      </p>

      <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-800" htmlFor="specialist-name">
            Specialist Name
          </label>
          <input
            id="specialist-name"
            type="text"
            className="mt-2 w-full rounded-md border border-slate-300 p-3 text-sm"
            placeholder="Research Specialist"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-800" htmlFor="specialist-soul">
            Soul Profile
          </label>
          <input
            id="specialist-soul"
            type="text"
            className="mt-2 w-full rounded-md border border-slate-300 p-3 text-sm"
            placeholder="Analytical and concise"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-800" htmlFor="specialist-prompt">
            Prompt
          </label>
          <textarea
            id="specialist-prompt"
            className="mt-2 min-h-24 w-full rounded-md border border-slate-300 p-3 text-sm"
            placeholder="How this specialist should approach delegated tasks..."
          />
        </div>
        <fieldset className="md:col-span-2">
          <legend className="text-sm font-medium text-slate-800">Capabilities</legend>
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-700">
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" />
              <span>delegate</span>
            </label>
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" />
              <span>write_memory</span>
            </label>
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" />
              <span>run_tool</span>
            </label>
          </div>
        </fieldset>
        <button
          type="button"
          className="md:col-span-2 rounded-md bg-slate-900 px-4 py-2 text-sm text-white"
        >
          Save Specialist Agent
        </button>
      </form>
    </section>
  )
}
