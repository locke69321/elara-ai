import argparse
import asyncio
import json
import statistics
import tempfile
import time
from pathlib import Path

from apps.api.memory import PostgresMemoryStore, SqliteMemoryStore


async def benchmark_store(
    *,
    name: str,
    store: SqliteMemoryStore,
    records: list[dict[str, object]],
    iterations: int,
) -> dict[str, float]:
    for record in records:
        await store.upsert_memory(
            workspace_id=str(record["workspace_id"]),
            agent_id=str(record["agent_id"]),
            memory_id=str(record["memory_id"]),
            content=str(record["content"]),
        )

    durations_ms: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        await store.search(
            workspace_id="ws-perf",
            agent_id="agent-perf",
            query="release approval checkpoint",
            top_k=5,
        )
        durations_ms.append((time.perf_counter() - started) * 1000)

    p95_ms = statistics.quantiles(durations_ms, n=100)[94] if len(durations_ms) >= 100 else max(durations_ms)
    return {
        "backend": name,
        "iterations": float(iterations),
        "p95_ms": round(p95_ms, 2),
        "mean_ms": round(statistics.mean(durations_ms), 2),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run memory retrieval benchmark")
    parser.add_argument(
        "--fixture",
        default="scripts/perf/fixtures/memory_fixture.json",
        help="Fixture JSON file path",
    )
    parser.add_argument("--iterations", type=int, default=150)
    args = parser.parse_args()

    records = json.loads(Path(args.fixture).read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_store = SqliteMemoryStore(database_path=f"{tmp_dir}/sqlite-memory.sqlite3")
        postgres_store = PostgresMemoryStore(database_path=f"{tmp_dir}/postgres-memory.sqlite3")

        sqlite_result = await benchmark_store(
            name="sqlite",
            store=sqlite_store,
            records=records,
            iterations=args.iterations,
        )
        postgres_result = await benchmark_store(
            name="postgres",
            store=postgres_store,
            records=records,
            iterations=args.iterations,
        )

    print(json.dumps([sqlite_result, postgres_result], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
