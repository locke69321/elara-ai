export type AgentRole = 'companion_primary' | 'executor_primary' | 'specialist'

export interface Workspace {
  id: string
  name: string
}

export interface AgentRunEvent {
  agentRunId: string
  seq: number
  eventType: string
  payload: Record<string, unknown>
}

export interface ReplayCursor {
  agentRunId: string
  lastSeq: number
}
