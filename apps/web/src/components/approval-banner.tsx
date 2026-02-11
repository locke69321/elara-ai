export function ApprovalBanner(props: {
  status: 'required' | 'approved' | 'idle'
  approvalId?: string
}) {
  if (props.status === 'idle') {
    return null
  }

  if (props.status === 'approved') {
    return (
      <aside className="approval-banner approved" data-testid="approval-approved">
        Approval recorded. Execution resumed for this goal.
      </aside>
    )
  }

  return (
    <aside className="approval-banner required" data-testid="approval-required">
      <strong>Approval Required</strong>
      <p>High-impact delegation is blocked until this request is approved.</p>
      <p className="approval-id">Request: {props.approvalId ?? 'pending-id'}</p>
    </aside>
  )
}
