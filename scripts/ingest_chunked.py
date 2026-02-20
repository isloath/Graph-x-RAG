#!/usr/bin/env python3
"""
Ingest a large applications JSON file in chunks to avoid "Empty reply from server"
when the single-request body is too large for the server/client.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest applications JSON in chunks")
    parser.add_argument("input", type=Path, help="Path to applications JSON (e.g. data/sample_applications.json)")
    parser.add_argument("--base-url", default="http://localhost:8001", help="API base URL")
    parser.add_argument("--chunk-size", type=int, default=1500, help="Applications per POST (default 1500)")
    args = parser.parse_args()

    path = args.input
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    applications = data.get("applications") or data
    if not isinstance(applications, list):
        print("Expected JSON with 'applications' array or a top-level array", file=sys.stderr)
        sys.exit(1)

    total = len(applications)
    url = f"{args.base_url.rstrip('/')}/api/v1/ingest"
    chunk_size = args.chunk_size
    total_ingested = 0

    with httpx.Client(timeout=300.0) as client:
        for i in range(0, total, chunk_size):
            chunk = applications[i : i + chunk_size]
            payload = {"applications": chunk}
            r = client.post(url, json=payload)
            r.raise_for_status()
            out = r.json()
            n = out.get("ingested", len(chunk))
            total_ingested += n
            print(f"Ingested {n} (total so far: {total_ingested}/{total})")

    print(f"Done. Total ingested: {total_ingested}")


if __name__ == "__main__":
    main()
