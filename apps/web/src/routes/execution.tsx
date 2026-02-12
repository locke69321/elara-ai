import { createFileRoute } from '@tanstack/react-router'

import { ApprovalBanner } from '../components/approval-banner'
import { TimelineEvent } from '../components/timeline-event'
import { postExecutionGoal } from '../lib/server/dual-mode'

export const Route = createFileRoute('/execution')({
  component: ExecutionPage,
})

function ExecutionPage() {
  const executionPreview = postExecutionGoal
  void executionPreview

  return (
    <section className="route-grid">
      <article className="panel">
        <h2>Execution Workflow</h2>
        <p>Submit goals, resume from sequence checkpoints, and inspect delegation events.</p>

        <label htmlFor="goal-input">Goal</label>
        <input
          id="goal-input"
          data-testid="execution-goal-input"
          type="text"
          placeholder="Describe what you want executed..."
        />
        <button type="button" data-testid="execution-submit-button">
          Execute Goal
        </button>

        <ApprovalBanner status="required" approvalId="approval-00042" />

        <div className="replay-controls" data-testid="replay-resume-controls">
          <div>
            <label htmlFor="last-seq">Replay from Sequence</label>
            <input id="last-seq" type="number" defaultValue={8} min={0} />
          </div>
          <button type="button" data-testid="replay-resume-button">
            Resume Replay
          </button>
        </div>
      </article>

      <article className="panel">
        <h3>Delegation Timeline</h3>
        <ul className="timeline-list" data-testid="execution-timeline">
          <TimelineEvent sequence={1} eventType="run.started" details="Goal accepted" />
          <TimelineEvent
            sequence={2}
            eventType="task.delegated"
            details="Assigned to Research Specialist"
          />
          <TimelineEvent sequence={3} eventType="task.completed" details="Specialist returned output" />
          <TimelineEvent sequence={4} eventType="run.completed" details="Execution summary generated" />
        </ul>
      </article>
    </section>
  )
}
