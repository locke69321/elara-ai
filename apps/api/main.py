from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from apps.api.agents import ActorContext, AgentRuntime, PolicyEngine, SpecialistAgent
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory import SqliteMemoryStore

Role = Literal["owner", "member"]
Capability = Literal[
    "read_memory",
    "write_memory",
    "run_tool",
    "delegate",
    "external_action",
]


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


class DelegatedTaskResultResponse(BaseModel):
    specialist_id: str
    specialist_name: str
    task: str
    output: str


class ExecutionGoalResponse(BaseModel):
    agent_run_id: str
    summary: str
    delegated_results: list[DelegatedTaskResultResponse]


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory_store = SqliteMemoryStore()
    policy_engine = PolicyEngine()
    outbox = AgentRunEventOutbox()
    app.state.runtime = AgentRuntime(
        memory_store=memory_store,
        policy_engine=policy_engine,
        outbox=outbox,
    )
    yield
    del app.state.runtime


app = FastAPI(
    title="Elara Agent API",
    version="0.1.0",
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
    return runtime


def get_actor(
    x_user_id: str = Header(default="local-owner"),
    x_user_role: str = Header(default="owner"),
) -> ActorContext:
    if x_user_role not in {"owner", "member"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-user-role must be owner or member",
        )

    return ActorContext(user_id=x_user_id, role=x_user_role)  # type: ignore[arg-type]


@app.get("/workspaces/{workspace_id}/specialists", response_model=list[SpecialistResponse])
async def list_specialists(
    workspace_id: str,
    runtime: AgentRuntime = Depends(get_runtime),
) -> list[SpecialistResponse]:
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
) -> SpecialistResponse:
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
) -> CompanionMessageResponse:
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
) -> ExecutionGoalResponse:
    try:
        result = await runtime.execute_goal(
            workspace_id=workspace_id,
            actor=actor,
            goal=payload.goal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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
) -> list[dict[str, object]]:
    if last_seq < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="last_seq must be >= 0",
        )

    return runtime.replay_events(agent_run_id=agent_run_id, last_seq=last_seq)
