from __future__ import annotations

import argparse
import json
import random
from datetime import UTC, datetime, timedelta

STATUSES = ["approved", "rejected", "disbursed"]


def maybe(value: str, p: float = 0.15) -> str | None:
    return None if random.random() < p else value


def generate(n: int) -> list[dict]:
    base_time = datetime.now(UTC) - timedelta(days=7)
    apps = []
    for i in range(n):
        idx = f"APP-{i:07d}"
        group = i % max(1, n // 20)
        apps.append(
            {
                "application_id": idx,
                "customer_id": f"CUS-{i:07d}",
                "created_at": (base_time + timedelta(seconds=i)).isoformat(),
                "phone": maybe(f"+1555{group:06d}", 0.2),
                "email": maybe(f"user{i}@mail.test", 0.25),
                "document_id": maybe(f"DOC-{group:05d}", 0.2),
                "device_id": maybe(f"DEV-{group % 15:04d}", 0.3),
                "bank_account": maybe(f"ACCT-{i % 1000:08d}", 0.1),
                "wallet_id": maybe(f"WAL-{i % 500:06d}", 0.1),
                "loan_amount": round(random.uniform(1000, 25000), 2),
                "status": random.choice(STATUSES),
            }
        )
    return apps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--count", type=int, default=1000)
    parser.add_argument("-o", "--output", type=str, default="data/sample_applications.json")
    args = parser.parse_args()

    payload = {"applications": generate(args.count)}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {args.count} applications to {args.output}")
