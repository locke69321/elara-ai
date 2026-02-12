const CAPABILITY_OPTIONS = ['delegate', 'write_memory', 'run_tool', 'external_action']

export function SpecialistForm(props: { ownerEditable: boolean }) {
  return (
    <form className="panel specialist-form" data-testid="specialist-form">
      <header>
        <h3>Specialist Configuration</h3>
        <p>Owner edits apply immediately to execution delegation policy.</p>
      </header>
      <label htmlFor="specialist-id">Specialist ID</label>
      <input id="specialist-id" placeholder="spec-research" />
      <label htmlFor="specialist-name">Name</label>
      <input id="specialist-name" placeholder="Research Specialist" />
      <label htmlFor="specialist-soul">Soul</label>
      <input id="specialist-soul" placeholder="Analytical and concise" />
      <label htmlFor="specialist-prompt">Prompt</label>
      <textarea id="specialist-prompt" rows={4} />
      <fieldset>
        <legend>Capabilities</legend>
        <div className="capability-grid">
          {CAPABILITY_OPTIONS.map((capability) => (
            <label key={capability}>
              <input
                type="checkbox"
                defaultChecked={capability === 'delegate'}
                disabled={!props.ownerEditable}
              />
              <span>{capability}</span>
            </label>
          ))}
        </div>
      </fieldset>
      {!props.ownerEditable ? (
        <p className="member-constraint">
          Member role can view specialist definitions, but only owners can edit.
        </p>
      ) : null}
      <button type="button" disabled={!props.ownerEditable}>
        Save Specialist
      </button>
    </form>
  )
}
