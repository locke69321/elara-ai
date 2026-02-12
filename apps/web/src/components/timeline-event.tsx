export function TimelineEvent(props: {
  sequence: number
  eventType: string
  details: string
  testId?: string
}) {
  return (
    <li className="timeline-event" data-testid={props.testId}>
      <span className="event-seq">#{props.sequence}</span>
      <div>
        <p className="event-type">{props.eventType}</p>
        <p className="event-details">{props.details}</p>
      </div>
    </li>
  )
}
