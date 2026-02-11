import { createFileRoute } from '@tanstack/react-router'

import { SpecialistForm } from '../components/specialist-form'
import { listSpecialists } from '../lib/server/dual-mode'

export const Route = createFileRoute('/agent-studio')({
  component: AgentStudioPage,
})

function AgentStudioPage() {
  const specialistsPreview = listSpecialists
  void specialistsPreview

  const specialistCards = [
    {
      id: 'spec-research',
      name: 'Research Specialist',
      soul: 'Analytical',
      capabilities: 'delegate, write_memory',
    },
    {
      id: 'spec-risk',
      name: 'Risk Specialist',
      soul: 'Cautious',
      capabilities: 'delegate, external_action',
    },
  ]

  return (
    <section className="route-grid">
      <article className="panel" data-testid="specialist-list">
        <h2>Specialists</h2>
        <p>Owner/member boundaries are shown per capability profile.</p>
        <ul>
          {specialistCards.map((specialist) => (
            <li key={specialist.id}>
              <strong>{specialist.name}</strong> ({specialist.id})
              <div>Soul: {specialist.soul}</div>
              <div>Capabilities: {specialist.capabilities}</div>
            </li>
          ))}
        </ul>
      </article>

      <SpecialistForm ownerEditable />
    </section>
  )
}
