export type AgentRole = 'companion_primary' | 'executor_primary' | 'specialist'
export type Capability =
  | 'read_memory'
  | 'write_memory'
  | 'run_tool'
  | 'delegate'
  | 'external_action'
export type ApprovalDecision = 'approved' | 'denied'

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
  approved_request_ids?: string[]
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

export interface Invitation {
  token: string
  workspace_id: string
  email: string
  role: 'member'
  invited_by: string
  created_at: string
  expires_at: string
  accepted: boolean
}

export interface Membership {
  workspace_id: string
  user_id: string
  role: 'member'
  invited_via: string
}

export interface ApprovalRequest {
  id: string
  workspace_id: string
  actor_id: string
  capability: Capability
  action: string
  reason: string
  status: 'pending' | 'approved' | 'denied'
  created_at: string
  decided_at: string | null
  decided_by: string | null
}

export interface AuditEvent {
  id: string
  workspace_id: string
  actor_id: string
  action: string
  outcome: string
  metadata: Record<string, unknown>
  previous_hash: string
  event_hash: string
  created_at: string
}
