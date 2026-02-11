from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Literal, cast

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from apps.api.agents import (
    ActorContext,
    AgentRuntime,
    PolicyEngine,
    SpecialistAgent,
    StubCompletionClient,
)
from apps.api.audit import ImmutableAuditLog
from apps.api.auth import InvitationService, WorkspaceAccessService
from apps.api.db.sqlite import enforce_sqlite_security_if_enabled
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory import SqliteMemoryStore
from apps.api.safety import ApprovalRequiredError, ApprovalService

Role = Literal["owner", "member"]
Capability = Literal[
    "read_memory",
    "write_memory",
    "run_tool",
    "delegate",
    "external_action",
]
ApprovalDecision = Literal["approved", "denied"]


class CompanionMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)


class CompanionMessageResponse(BaseModel):
    response: str
    memory_hits: list[str]


class SpecialistPayload(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=4_000)
    soul: str = Field(min_length=1, max_length=512)
    capabilities: list[Capability] = Field(default_factory=list)


class SpecialistResponse(BaseModel):
    id: str
    name: str
    prompt: str
    soul: str
    capabilities: list[Capability]


class ExecutionGoalRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=2_000)
    approved_request_ids: list[str] = Field(default_factory=list)


class DelegatedTaskResultResponse(BaseModel):
    specialist_id: str
    specialist_name: str
    task: str
    output: str


class ExecutionGoalResponse(BaseModel):
    agent_run_id: str
    summary: str
    delegated_results: list[DelegatedTaskResultResponse]


class InvitationCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class InvitationResponse(BaseModel):
    token: str
    workspace_id: str
    email: str
    role: str
    invited_by: str
    created_at: str
    expires_at: str
    accepted: bool


class InvitationAcceptRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)


class MembershipResponse(BaseModel):
    workspace_id: str
    user_id: str
    role: str
    invited_via: str


class ApprovalCreateRequest(BaseModel):
    capability: Capability
    action: str = Field(min_length=3, max_length=512)
    reason: str = Field(min_length=3, max_length=512)


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecision


class ApprovalResponse(BaseModel):
    id: str
    workspace_id: str
    actor_id: str
    capability: Capability
    action: str
    reason: str
    status: str
    created_at: str
    decided_at: str | None
    decided_by: str | None


class AuditEventResponse(BaseModel):
    id: str
    workspace_id: str
    actor_id: str
    action: str
    outcome: str
    metadata: dict[str, object]
    previous_hash: str
    event_hash: str
    created_at: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    enforce_sqlite_security_if_enabled()

    memory_store = SqliteMemoryStore()
    policy_engine = PolicyEngine()
    outbox = AgentRunEventOutbox()
    completion_client = StubCompletionClient()
    approval_service = ApprovalService()
    audit_log = ImmutableAuditLog()
    invitation_service = InvitationService()
    workspace_access_service = WorkspaceAccessService()

    app.state.runtime = AgentRuntime(
        memory_store=memory_store,
        policy_engine=policy_engine,
        outbox=outbox,
        completion_client=completion_client,
        approval_service=approval_service,
        audit_log=audit_log,
    )
    app.state.approvals = approval_service
    app.state.audit_log = audit_log
    app.state.invitations = invitation_service
    app.state.workspace_access = workspace_access_service
    yield
    del app.state.runtime
    del app.state.approvals
    del app.state.audit_log
    del app.state.invitations
    del app.state.workspace_access


app = FastAPI(
    title="Elara Agent API",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def get_runtime(request: Request) -> AgentRuntime:
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="runtime unavailable",
        )
    return cast(AgentRuntime, runtime)


def get_approvals(request: Request) -> ApprovalService:
    approvals = getattr(request.app.state, "approvals", None)
    if approvals is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="approvals service unavailable",
        )
    return cast(ApprovalService, approvals)


def get_audit_log(request: Request) -> ImmutableAuditLog:
    audit_log = getattr(request.app.state, "audit_log", None)
    if audit_log is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="audit service unavailable",
        )
    return cast(ImmutableAuditLog, audit_log)


def get_invitations(request: Request) -> InvitationService:
    invitations = getattr(request.app.state, "invitations", None)
    if invitations is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="invitation service unavailable",
        )
    return cast(InvitationService, invitations)


def get_workspace_access(request: Request) -> WorkspaceAccessService:
    workspace_access = getattr(request.app.state, "workspace_access", None)
    if workspace_access is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="workspace access service unavailable",
        )
    return cast(WorkspaceAccessService, workspace_access)


def get_actor(
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> ActorContext:
    if x_user_id is None or x_user_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="x-user-id and x-user-role headers are required",
        )

    if x_user_role not in {"owner", "member"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-user-role must be owner or member",
        )

    return ActorContext(user_id=x_user_id, role=cast(Role, x_user_role))


def invitation_token_fingerprint(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()[:12]


def authorize_workspace_access(
    *,
    workspace_id: str,
    actor: ActorContext,
    workspace_access: WorkspaceAccessService,
) -> None:
    try:
        workspace_access.ensure_workspace_access(
            workspace_id=workspace_id,
            actor=actor,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@app.get("/workspaces/{workspace_id}/specialists", response_model=list[SpecialistResponse])
async def list_specialists(
    workspace_id: str,
    runtime: AgentRuntime = Depends(get_runtime),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> list[SpecialistResponse]:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    specialists = runtime.list_specialists(workspace_id=workspace_id)
    return [
        SpecialistResponse(
            id=specialist.id,
            name=specialist.name,
            prompt=specialist.prompt,
            soul=specialist.soul,
            capabilities=sorted(specialist.capabilities),
        )
        for specialist in specialists
    ]


@app.post(
    "/workspaces/{workspace_id}/specialists",
    response_model=SpecialistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_specialist(
    workspace_id: str,
    payload: SpecialistPayload,
    runtime: AgentRuntime = Depends(get_runtime),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> SpecialistResponse:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    specialist = SpecialistAgent(
        id=payload.id,
        name=payload.name,
        prompt=payload.prompt,
        soul=payload.soul,
        capabilities=set(payload.capabilities),
    )
    try:
        stored = runtime.upsert_specialist(
            workspace_id=workspace_id,
            actor=actor,
            specialist=specialist,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return SpecialistResponse(
        id=stored.id,
        name=stored.name,
        prompt=stored.prompt,
        soul=stored.soul,
        capabilities=sorted(stored.capabilities),
    )


@app.post(
    "/workspaces/{workspace_id}/companion/messages",
    response_model=CompanionMessageResponse,
)
async def send_companion_message(
    workspace_id: str,
    payload: CompanionMessageRequest,
    runtime: AgentRuntime = Depends(get_runtime),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> CompanionMessageResponse:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    reply = await runtime.companion_message(
        workspace_id=workspace_id,
        actor_id=actor.user_id,
        message=payload.message,
    )
    return CompanionMessageResponse(response=reply.response, memory_hits=reply.memory_hits)


@app.post(
    "/workspaces/{workspace_id}/execution/goals",
    response_model=ExecutionGoalResponse,
)
async def execute_goal(
    workspace_id: str,
    payload: ExecutionGoalRequest,
    runtime: AgentRuntime = Depends(get_runtime),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> ExecutionGoalResponse:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    try:
        result = await runtime.execute_goal(
            workspace_id=workspace_id,
            actor=actor,
            goal=payload.goal,
            approved_request_ids=set(payload.approved_request_ids),
        )
    except ApprovalRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "approval_id": exc.approval_id,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ExecutionGoalResponse(
        agent_run_id=result.agent_run_id,
        summary=result.summary,
        delegated_results=[
            DelegatedTaskResultResponse(
                specialist_id=item.specialist_id,
                specialist_name=item.specialist_name,
                task=item.task,
                output=item.output,
            )
            for item in result.delegated_results
        ],
    )


@app.get("/agent-runs/{agent_run_id}/events")
async def replay_events(
    agent_run_id: str,
    last_seq: int = 0,
    runtime: AgentRuntime = Depends(get_runtime),
    actor: ActorContext = Depends(get_actor),
) -> list[dict[str, object]]:
    if last_seq < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="last_seq must be >= 0",
        )

    try:
        return runtime.replay_events(
            agent_run_id=agent_run_id,
            actor=actor,
            last_seq=last_seq,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@app.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    workspace_id: str,
    payload: InvitationCreateRequest,
    invitations: InvitationService = Depends(get_invitations),
    audit_log: ImmutableAuditLog = Depends(get_audit_log),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> InvitationResponse:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    if actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")

    invitation = invitations.create_invitation(
        workspace_id=workspace_id,
        email=payload.email,
        invited_by=actor.user_id,
    )
    audit_log.append_event(
        workspace_id=workspace_id,
        actor_id=actor.user_id,
        action="invitation.created",
        outcome="success",
        metadata={
            "email": payload.email,
            "token_fingerprint": invitation_token_fingerprint(invitation.token),
        },
    )
    return InvitationResponse(
        token=invitation.token,
        workspace_id=invitation.workspace_id,
        email=invitation.email,
        role=invitation.role,
        invited_by=invitation.invited_by,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        accepted=invitation.accepted,
    )


@app.get("/workspaces/{workspace_id}/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    workspace_id: str,
    invitations: InvitationService = Depends(get_invitations),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> list[InvitationResponse]:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    if actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")

    records = invitations.list_invitations(workspace_id=workspace_id)
    return [
        InvitationResponse(
            token=record.token,
            workspace_id=record.workspace_id,
            email=record.email,
            role=record.role,
            invited_by=record.invited_by,
            created_at=record.created_at,
            expires_at=record.expires_at,
            accepted=record.accepted,
        )
        for record in records
    ]


@app.post("/invitations/{token}/accept", response_model=MembershipResponse)
async def accept_invitation(
    token: str,
    payload: InvitationAcceptRequest,
    invitations: InvitationService = Depends(get_invitations),
    audit_log: ImmutableAuditLog = Depends(get_audit_log),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> MembershipResponse:
    try:
        membership = invitations.accept_invitation(token=token, user_id=payload.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    audit_log.append_event(
        workspace_id=membership.workspace_id,
        actor_id=payload.user_id,
        action="invitation.accepted",
        outcome="success",
        metadata={
            "token_fingerprint": invitation_token_fingerprint(token),
            "role": membership.role,
        },
    )
    workspace_access.add_workspace_member(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
    )
    return MembershipResponse(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        invited_via=membership.invited_via,
    )


@app.post(
    "/workspaces/{workspace_id}/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_approval(
    workspace_id: str,
    payload: ApprovalCreateRequest,
    approvals: ApprovalService = Depends(get_approvals),
    audit_log: ImmutableAuditLog = Depends(get_audit_log),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> ApprovalResponse:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    request = approvals.create_request(
        workspace_id=workspace_id,
        actor_id=actor.user_id,
        capability=payload.capability,
        action=payload.action,
        reason=payload.reason,
    )
    audit_log.append_event(
        workspace_id=workspace_id,
        actor_id=actor.user_id,
        action="approval.created",
        outcome="pending",
        metadata={"approval_id": request.id, "capability": payload.capability},
    )
    return ApprovalResponse(
        id=request.id,
        workspace_id=request.workspace_id,
        actor_id=request.actor_id,
        capability=request.capability,
        action=request.action,
        reason=request.reason,
        status=request.status,
        created_at=request.created_at,
        decided_at=request.decided_at,
        decided_by=request.decided_by,
    )


@app.post("/approvals/{approval_id}/decision", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    approvals: ApprovalService = Depends(get_approvals),
    audit_log: ImmutableAuditLog = Depends(get_audit_log),
    actor: ActorContext = Depends(get_actor),
) -> ApprovalResponse:
    if actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")

    try:
        decided = approvals.decide_request(
            approval_id=approval_id,
            approver_id=actor.user_id,
            decision=payload.decision,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    audit_log.append_event(
        workspace_id=decided.workspace_id,
        actor_id=actor.user_id,
        action="approval.decided",
        outcome=decided.status,
        metadata={"approval_id": decided.id},
    )
    return ApprovalResponse(
        id=decided.id,
        workspace_id=decided.workspace_id,
        actor_id=decided.actor_id,
        capability=decided.capability,
        action=decided.action,
        reason=decided.reason,
        status=decided.status,
        created_at=decided.created_at,
        decided_at=decided.decided_at,
        decided_by=decided.decided_by,
    )


@app.get("/workspaces/{workspace_id}/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    workspace_id: str,
    approvals: ApprovalService = Depends(get_approvals),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> list[ApprovalResponse]:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    if actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")

    records = approvals.list_requests(workspace_id=workspace_id)
    return [
        ApprovalResponse(
            id=record.id,
            workspace_id=record.workspace_id,
            actor_id=record.actor_id,
            capability=record.capability,
            action=record.action,
            reason=record.reason,
            status=record.status,
            created_at=record.created_at,
            decided_at=record.decided_at,
            decided_by=record.decided_by,
        )
        for record in records
    ]


@app.get("/workspaces/{workspace_id}/audit-events", response_model=list[AuditEventResponse])
async def list_audit_events(
    workspace_id: str,
    audit_log: ImmutableAuditLog = Depends(get_audit_log),
    actor: ActorContext = Depends(get_actor),
    workspace_access: WorkspaceAccessService = Depends(get_workspace_access),
) -> list[AuditEventResponse]:
    authorize_workspace_access(
        workspace_id=workspace_id,
        actor=actor,
        workspace_access=workspace_access,
    )
    if actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")

    events = audit_log.list_events(workspace_id=workspace_id)
    return [
        AuditEventResponse(
            id=event.id,
            workspace_id=event.workspace_id,
            actor_id=event.actor_id,
            action=event.action,
            outcome=event.outcome,
            metadata=event.metadata,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
            created_at=event.created_at,
        )
        for event in events
    ]
