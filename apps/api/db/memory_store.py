from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MemoryItem:
    workspace_id: str
    agent_id: str
    memory_id: str
    content: str


@dataclass(frozen=True)
class MemoryMatch:
    memory_id: str
    score: float
    content: str


class MemoryStore(Protocol):
    async def upsert_memory(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        memory_id: str,
        content: str,
    ) -> MemoryItem: ...

    async def search(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[MemoryMatch]: ...
