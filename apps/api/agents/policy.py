from dataclasses import dataclass
from typing import Literal

Capability = Literal[
    "read_memory",
    "write_memory",
    "run_tool",
    "delegate",
    "external_action",
]
Role = Literal["owner", "member"]

HIGH_IMPACT_CAPABILITIES: set[Capability] = {"run_tool", "external_action"}
DEFAULT_TOOL_ALLOWLIST: set[str] = {
    "search_docs",
    "summarize_text",
    "workspace_audit_lookup",
}


@dataclass(frozen=True)
class ActorContext:
    user_id: str
    role: Role


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None
    requires_approval: bool = False


class PolicyEngine:
    """Default-deny decisions for delegation and specialist configuration."""

    def __init__(self, *, allowed_tools: set[str] | None = None) -> None:
        self._allowed_tools = allowed_tools if allowed_tools is not None else DEFAULT_TOOL_ALLOWLIST

    def can_edit_specialists(self, actor: ActorContext) -> PolicyDecision:
        if actor.role != "owner":
            return PolicyDecision(
                allowed=False,
                reason="only owners can create or edit specialist agents",
            )
        return PolicyDecision(allowed=True)

    def can_delegate(
        self,
        *,
        actor: ActorContext,
        capabilities: set[Capability],
    ) -> PolicyDecision:
        if "delegate" not in capabilities:
            return PolicyDecision(
                allowed=False,
                reason="specialist missing delegate capability",
            )

        if actor.role not in {"owner", "member"}:
            return PolicyDecision(allowed=False, reason="unsupported actor role")

        if actor.role == "member" and capabilities.intersection(HIGH_IMPACT_CAPABILITIES):
            return PolicyDecision(
                allowed=False,
                reason="members cannot delegate high-impact capabilities",
            )

        requires_approval = bool(capabilities.intersection(HIGH_IMPACT_CAPABILITIES))
        return PolicyDecision(allowed=True, requires_approval=requires_approval)

    def can_use_tool(self, *, tool_name: str) -> PolicyDecision:
        if tool_name in self._allowed_tools:
            return PolicyDecision(allowed=True)
        return PolicyDecision(
            allowed=False,
            reason="tool is not in allowlist",
        )
