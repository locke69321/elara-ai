import { createServerFn } from '@tanstack/react-start'

export const postCompanionMessage = createServerFn({ method: 'POST' }).handler(
  async () => {
    return {
      response: 'Companion response placeholder',
      memory_hits: ['memory-1', 'memory-2'],
    }
  },
)

export const postExecutionGoal = createServerFn({ method: 'POST' }).handler(
  async () => {
    return {
      agent_run_id: 'run-sample',
      summary: 'Completed goal with 1 delegated specialist contribution(s).',
      delegated_results: [
        {
          specialist_id: 'spec-research',
          specialist_name: 'Research Specialist',
          task: "Subtask 1: contribute to goal 'sample'",
          output: 'Delegated output placeholder',
        },
      ],
      requires_approval: false,
    }
  },
)

export const listSpecialists = createServerFn({ method: 'GET' }).handler(
  async () => {
    return [
      {
        id: 'spec-research',
        name: 'Research Specialist',
        soul: 'Analytical',
        capabilities: ['delegate', 'write_memory'],
      },
      {
        id: 'spec-risk',
        name: 'Risk Specialist',
        soul: 'Cautious',
        capabilities: ['delegate', 'external_action'],
      },
    ]
  },
)
