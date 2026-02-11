from dataclasses import asdict, dataclass, field
from uuid import uuid4

from apps.api.agents.completion import CompletionClient
from apps.api.agents.policy import ActorContext, Capability, PolicyEngine
from apps.api.audit import ImmutableAuditLog
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory.store_base import MemoryStore
from apps.api.safety import ApprovalRequiredError, ApprovalService


@dataclass(frozen=True)
class SpecialistAgent:
    id: str
    name: str
    prompt: str
    soul: str
    capabilities: set[Capability] = field(default_factory=set)


@dataclass(frozen=True)
class DelegatedTaskResult:
    specialist_id: str
    specialist_name: str
    task: str
    output: str


@dataclass(frozen=True)
class CompanionReply:
    response: str
    memory_hits: list[str]


@dataclass(frozen=True)
class ExecutionReply:
    agent_run_id: str
    summary: str
    delegated_results: list[DelegatedTaskResult]


class AgentRuntime:
    def __init__(
        self,
        *,
        memory_store: MemoryStore,
        policy_engine: PolicyEngine,
        outbox: AgentRunEventOutbox,
        completion_client: CompletionClient,
        approval_service: ApprovalService,
        audit_log: ImmutableAuditLog,
    ) -> None:
        self._memory_store = memory_store
        self._policy = policy_engine
        self._outbox = outbox
        self._completion_client = completion_client
        self._approvals = approval_service
        self._audit = audit_log
        self._specialists_by_workspace: dict[str, dict[str, SpecialistAgent]] = {}
        self._run_workspace_by_id: dict[str, str] = {}
        self._run_actor_ids_by_id: dict[str, set[str]] = {}

    def _grant_run_access(self, *, agent_run_id: str, workspace_id: str, actor_id: str) -> None:
        self._run_workspace_by_id[agent_run_id] = workspace_id
        actors = self._run_actor_ids_by_id.setdefault(agent_run_id, set())
        actors.add(actor_id)

    def list_specialists(self, *, workspace_id: str) -> list[SpecialistAgent]:
        specialists = self._specialists_by_workspace.get(workspace_id, {})
        return sorted(specialists.values(), key=lambda specialist: specialist.id)

    def upsert_specialist(
        self,
        *,
        workspace_id: str,
        actor: ActorContext,
        specialist: SpecialistAgent,
    ) -> SpecialistAgent:
        decision = self._policy.can_edit_specialists(actor)
        if not decision.allowed:
            raise PermissionError(decision.reason)

        workspace_agents = self._specialists_by_workspace.setdefault(workspace_id, {})
        workspace_agents[specialist.id] = specialist
        self._audit.append_event(
            workspace_id=workspace_id,
            actor_id=actor.user_id,
            action="specialist.upserted",
            outcome="success",
            metadata={
                "specialist_id": specialist.id,
                "capabilities": sorted(specialist.capabilities),
            },
        )
        return specialist

    async def companion_message(
        self,
        *,
        workspace_id: str,
        actor_id: str,
        message: str,
    ) -> CompanionReply:
        memory_id = f"memory-{uuid4()}"
        await self._memory_store.upsert_memory(
            workspace_id=workspace_id,
            agent_id="companion_primary",
            memory_id=memory_id,
            content=message,
        )

        matches = await self._memory_store.search(
            workspace_id=workspace_id,
            agent_id="companion_primary",
            query=message,
            top_k=3,
        )
        memory_hits = [match.memory_id for match in matches]

        completion = await self._completion_client.complete(
            system_prompt="companion_primary",
            user_input=message,
        )
        response = f"I hear you, {actor_id}. {completion} ({len(memory_hits)} memory hit(s))."

        self._outbox.append_event(
            agent_run_id=f"companion-{workspace_id}",
            event_type="companion.message",
            payload={"memory_hit_count": len(memory_hits)},
        )
        self._grant_run_access(
            agent_run_id=f"companion-{workspace_id}",
            workspace_id=workspace_id,
            actor_id=actor_id,
        )
        self._audit.append_event(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="companion.message",
            outcome="success",
            metadata={"memory_hit_count": len(memory_hits)},
        )

        return CompanionReply(response=response, memory_hits=memory_hits)

    async def execute_goal(
        self,
        *,
        workspace_id: str,
        actor: ActorContext,
        goal: str,
        approved_request_ids: set[str] | None = None,
    ) -> ExecutionReply:
        approved_ids = approved_request_ids or set()
        specialists = self.list_specialists(workspace_id=workspace_id)
        eligible_specialists: list[tuple[SpecialistAgent, bool]] = []
        for specialist in specialists:
            decision = self._policy.can_delegate(
                actor=actor,
                capabilities=specialist.capabilities,
            )
            if decision.allowed:
                eligible_specialists.append((specialist, decision.requires_approval))

        if not eligible_specialists:
            self._audit.append_event(
                workspace_id=workspace_id,
                actor_id=actor.user_id,
                action="goal.execute",
                outcome="rejected",
                metadata={"reason": "no eligible specialists"},
            )
            raise ValueError("no specialist agents are eligible for delegation")

        for specialist, requires_approval in eligible_specialists:
            if not requires_approval:
                continue

            capability: Capability = (
                "external_action"
                if "external_action" in specialist.capabilities
                else "run_tool"
            )
            action_scope = f"delegate:{specialist.id}:{goal}"
            has_approval = any(
                self._approvals.is_approved(
                    approval_id=approval_id,
                    workspace_id=workspace_id,
                    actor_id=actor.user_id,
                    capability=capability,
                    action=action_scope,
                )
                for approval_id in approved_ids
            )
            if has_approval:
                continue

            request = self._approvals.create_request(
                workspace_id=workspace_id,
                actor_id=actor.user_id,
                capability=capability,
                action=action_scope,
                reason="high-impact delegation requires explicit approval",
            )
            self._audit.append_event(
                workspace_id=workspace_id,
                actor_id=actor.user_id,
                action="approval.requested",
                outcome="pending",
                metadata={
                    "approval_id": request.id,
                    "specialist_id": specialist.id,
                    "capability": capability,
                },
            )
            raise ApprovalRequiredError(
                request.id,
                "high-impact delegation requires explicit approval",
            )

        agent_run_id = f"run-{uuid4()}"
        self._grant_run_access(
            agent_run_id=agent_run_id,
            workspace_id=workspace_id,
            actor_id=actor.user_id,
        )
        self._outbox.append_event(
            agent_run_id=agent_run_id,
            event_type="run.started",
            payload={"goal": goal, "actor_id": actor.user_id},
        )
        self._audit.append_event(
            workspace_id=workspace_id,
            actor_id=actor.user_id,
            action="goal.execute",
            outcome="started",
            metadata={"agent_run_id": agent_run_id, "goal": goal},
        )

        delegated_results: list[DelegatedTaskResult] = []
        for index, specialist_entry in enumerate(eligible_specialists[:2], start=1):
            specialist = specialist_entry[0]
            task = f"Subtask {index}: contribute to goal '{goal}'"
            self._outbox.append_event(
                agent_run_id=agent_run_id,
                event_type="task.delegated",
                payload={"specialist_id": specialist.id, "task": task},
            )

            output = await self._completion_client.complete(
                system_prompt=f"{specialist.prompt} | soul={specialist.soul}",
                user_input=task,
            )
            delegated = DelegatedTaskResult(
                specialist_id=specialist.id,
                specialist_name=specialist.name,
                task=task,
                output=output,
            )
            delegated_results.append(delegated)

            self._outbox.append_event(
                agent_run_id=agent_run_id,
                event_type="task.completed",
                payload=asdict(delegated),
            )
            self._audit.append_event(
                workspace_id=workspace_id,
                actor_id=actor.user_id,
                action="task.delegated",
                outcome="completed",
                metadata={
                    "agent_run_id": agent_run_id,
                    "specialist_id": specialist.id,
                    "task": task,
                },
            )

        summary = (
            f"Completed goal with {len(delegated_results)} delegated "
            "specialist contribution(s)."
        )
        self._outbox.append_event(
            agent_run_id=agent_run_id,
            event_type="run.completed",
            payload={"summary": summary},
        )
        self._audit.append_event(
            workspace_id=workspace_id,
            actor_id=actor.user_id,
            action="goal.execute",
            outcome="completed",
            metadata={"agent_run_id": agent_run_id, "summary": summary},
        )

        return ExecutionReply(
            agent_run_id=agent_run_id,
            summary=summary,
            delegated_results=delegated_results,
        )

    def replay_events(
        self,
        *,
        agent_run_id: str,
        actor: ActorContext,
        last_seq: int = 0,
    ) -> list[dict[str, object]]:
        authorized_actor_ids = self._run_actor_ids_by_id.get(agent_run_id)
        if authorized_actor_ids is not None and actor.user_id not in authorized_actor_ids:
            raise PermissionError("actor is not authorized to replay this run")

        events = self._outbox.replay(agent_run_id=agent_run_id, last_seq=last_seq)
        return [
            {
                "agent_run_id": event.agent_run_id,
                "seq": event.seq,
                "event_type": event.event_type,
                "payload": event.payload,
                "created_at": event.created_at,
            }
            for event in events
        ]
