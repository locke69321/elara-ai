from typing import Protocol


class CompletionClient(Protocol):
    async def complete(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> str: ...


class StubCompletionClient:
    """Deterministic local completion stub used for development and tests."""

    async def complete(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> str:
        return f"[{system_prompt}] {user_input}"

