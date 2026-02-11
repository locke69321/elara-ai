export type AgentRole = 'companion_primary' | 'executor_primary' | 'specialist'
export type Capability =
  | 'read_memory'
  | 'write_memory'
  | 'run_tool'
  | 'delegate'
  | 'external_action'

export interface Workspace {
  id: string
  name: string
}

export interface SpecialistAgent {
  id: string
  name: string
  prompt: string
  soul: string
  capabilities: Capability[]
}

export interface AgentRunEvent {
  agent_run_id: string
  seq: number
  event_type: string
  payload: Record<string, unknown>
}

export interface ReplayCursor {
  agent_run_id: string
  last_seq: number
}

export interface CompanionMessageRequest {
  message: string
}

export interface CompanionMessageResponse {
  response: string
  memory_hits: string[]
}

export interface ExecutionGoalRequest {
  goal: string
}

export interface DelegatedTaskResult {
  specialist_id: string
  specialist_name: string
  task: string
  output: string
}

export interface ExecutionGoalResponse {
  agent_run_id: string
  summary: string
  delegated_results: DelegatedTaskResult[]
}
