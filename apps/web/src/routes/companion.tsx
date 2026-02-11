import { createFileRoute } from '@tanstack/react-router'

import { MemoryHitChip } from '../components/memory-hit-chip'
import { postCompanionMessage } from '../lib/server/dual-mode'

export const Route = createFileRoute('/companion')({
  component: CompanionPage,
})

function CompanionPage() {
  const conversation = [
    {
      id: 'msg-1',
      speaker: 'owner',
      text: 'Summarize what changed in approvals this week.',
    },
    {
      id: 'msg-2',
      speaker: 'companion',
      text: 'Approval requests increased after specialist run_tool enablement.',
    },
  ]

  const messagePreview = postCompanionMessage
  void messagePreview

  return (
    <section className="route-grid">
      <article className="panel">
        <h2>Companion Console</h2>
        <p>Conversational memory hits are visible so decisions stay reviewable.</p>
        <ul>
          {conversation.map((entry) => (
            <li key={entry.id}>
              <strong>{entry.speaker}</strong>: {entry.text}
            </li>
          ))}
        </ul>
      </article>

      <form className="panel">
        <h3>Send Message</h3>
        <label htmlFor="companion-message">Message</label>
        <textarea
          id="companion-message"
          data-testid="companion-message-input"
          rows={5}
          placeholder="Send a message to your companion agent..."
        />
        <div aria-label="memory hit chips">
          <MemoryHitChip memoryId="memory-102" />
          <MemoryHitChip memoryId="memory-119" />
        </div>
        <button type="button" data-testid="send-companion-message">
          Send Companion Message
        </button>
      </form>
    </section>
  )
}
