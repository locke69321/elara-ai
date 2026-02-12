import argparse
import statistics
import time

from fastapi.testclient import TestClient

from apps.api.main import app


def percentile_95(values: list[float]) -> float:
    if len(values) >= 100:
        return statistics.quantiles(values, n=100)[94]
    return max(values)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run API latency benchmark")
    parser.add_argument("--iterations", type=int, default=120)
    args = parser.parse_args()

    durations_ms: list[float] = []
    with TestClient(app) as client:
        for _ in range(args.iterations):
            started = time.perf_counter()
            response = client.post(
                "/workspaces/ws-perf/companion/messages",
                json={"message": "capture latency benchmark context"},
                headers={"x-user-id": "owner-perf", "x-user-role": "owner"},
            )
            if response.status_code != 200:
                raise RuntimeError(f"unexpected status code: {response.status_code}")
            durations_ms.append((time.perf_counter() - started) * 1000)

    p95_ms = percentile_95(durations_ms)
    summary = {
        "iterations": args.iterations,
        "mean_ms": round(statistics.mean(durations_ms), 2),
        "p95_ms": round(p95_ms, 2),
    }
    print(summary)


if __name__ == "__main__":
    main()
