from apps.api.events.outbox import AgentRunEventOutbox


async def run_once(outbox: AgentRunEventOutbox) -> list[str]:
    """Drain outbox messages and return run-local delivery IDs for observability."""

    drained = outbox.drain_outbox()
    return [f"{event.agent_run_id}:{event.seq}" for event in drained]
