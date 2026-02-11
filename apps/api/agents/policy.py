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

        requires_approval = bool(capabilities.intersection(HIGH_IMPACT_CAPABILITIES))
        return PolicyDecision(allowed=True, requires_approval=requires_approval)
