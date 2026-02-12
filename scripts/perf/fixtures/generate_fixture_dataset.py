import argparse
import json
from pathlib import Path


def build_record(index: int) -> dict[str, object]:
    return {
        "workspace_id": "ws-perf",
        "agent_id": "agent-perf",
        "memory_id": f"memory-{index:05d}",
        "content": (
            "release planning execution timeline "
            f"approval safety checkpoint {index}"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate perf fixture dataset")
    parser.add_argument(
        "--output",
        default="scripts/perf/fixtures/memory_fixture.json",
        help="Output JSON fixture path",
    )
    parser.add_argument("--count", type=int, default=300, help="Number of memory rows")
    args = parser.parse_args()

    records = [build_record(index) for index in range(args.count)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Generated {len(records)} fixture records at {output}")


if __name__ == "__main__":
    main()
