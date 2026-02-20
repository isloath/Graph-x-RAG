from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def chunks(items: list[dict], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunked ingest helper for Graph RAG API")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    payload = json.loads(args.json_path.read_text(encoding="utf-8"))
    applications = payload.get("applications", [])
    if not isinstance(applications, list):
        raise ValueError("Input JSON must have an 'applications' list")

    total = 0
    with httpx.Client(timeout=args.timeout) as client:
        for batch_idx, batch in enumerate(chunks(applications, args.chunk_size), start=1):
            r = client.post(
                f"{args.base_url.rstrip('/')}/api/v1/ingest",
                json={"applications": batch},
            )
            if r.status_code >= 400:
                print(f"Batch {batch_idx} failed: status={r.status_code}")
                print(r.text[:2000])
                r.raise_for_status()
            total += len(batch)
            print(f"Ingested batch {batch_idx}: {len(batch)} records (total={total})")

    print(f"Done. Total ingested: {total}")


if __name__ == "__main__":
    main()
