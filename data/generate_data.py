#!/usr/bin/env python3
"""Deterministic synthetic data generator for the Northwind Outfitters PoC.

Produces, from a single seed (``SEED = 42``), a Northwind-scale dataset that the simulation harness
runs against:

* ``data/orders.csv``             - 3,000 orders across 1,200 customers (order history + LTV).
* ``data/requests_baseline.csv``  - 4,000 support requests over one month, with the six recurring
  P3 topics weighted to ~62% of volume, a realistic channel mix, an email-inbox baseline (round-robin
  assignment, no priority) and free text the deflection assistant can classify.

Everything is derived from the seeded RNG, so re-running produces byte-identical files.
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

SEED = 42
N_ORDERS = 3000
N_CUSTOMERS = 1200
N_REQUESTS = 4000
N_AGENTS = 12
MONTH_START = datetime(2026, 2, 1, 0, 0, 0)
MONTH_DAYS = 30
PROSPECT_SHARE = 0.15

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

# (product family, share of orders, (lognormal mean USD, sigma), warranty months)
FAMILIES = [
    ("Footwear", 0.25, (170.0, 0.45), 12),
    ("Apparel", 0.25, (110.0, 0.50), 12),
    ("Camping", 0.20, (320.0, 0.55), 24),
    ("Climbing", 0.15, (250.0, 0.60), 24),
    ("Accessories", 0.15, (45.0, 0.60), 6),
]

# The six recurring P3 topics sum to 0.62; "Other" carries the rest.
TOPIC_WEIGHTS = {
    "Order Status": 0.15,
    "Return": 0.12,
    "Shipping": 0.10,
    "Sizing": 0.09,
    "Warranty": 0.08,
    "Store Hours": 0.08,
    "Other": 0.38,
}

CHANNEL_WEIGHTS = {"Email": 0.55, "Web": 0.18, "Chat": 0.15, "Phone": 0.12}

TEXTS: dict[str, list[str]] = {
    "Order Status": [
        "Where is my order? It was supposed to arrive last week.",
        "Can you tell me the status of my recent order?",
        "My package has not arrived yet, can you check where it is?",
        "I ordered a jacket and have not heard anything since. Has it shipped?",
        "Tracking has said pending for five days, any update on my order?",
    ],
    "Return": [
        "I want to return the boots I bought, they do not fit.",
        "How do I send back an item for a refund?",
        "I need to start a return for my last order.",
        "Can I exchange this jacket for a different color?",
        "I would like my money back for the tent I ordered.",
    ],
    "Warranty": [
        "My hiking boots split after three months, is that covered by warranty?",
        "The zipper broke on my jacket, can I get it repaired under warranty?",
        "Is my tent still under warranty? The pole snapped.",
        "My backpack strap tore, is this a warranty claim?",
        "Does the warranty cover a cracked camp stove?",
    ],
    "Shipping": [
        "How long does standard shipping take to Montana?",
        "What shipping options do you offer for expedited delivery?",
        "Do you ship to Canada and how much is postage?",
        "When will my order arrive if I choose express shipping?",
        "Is free shipping available on large orders?",
    ],
    "Sizing": [
        "How do your boots run, should I size up?",
        "What size jacket should I order if I am between medium and large?",
        "Do you have a sizing chart for the climbing harness?",
        "Are the pants true to size?",
        "Can you help me pick the right fit for a sleeping bag?",
    ],
    "Store Hours": [
        "What time do you open on Saturday?",
        "Are you open on Sundays?",
        "What are the store hours for the Bozeman location?",
        "When does the downtown store close today?",
        "Do you have a store near Denver and what are its hours?",
    ],
    "Other": [
        "I would like to speak to someone about a bulk order for my company.",
        "Do you offer gift cards?",
        "I have a question about my loyalty points.",
        "Can I change the email address on my account?",
        "Do you price match?",
        "I am having trouble logging into my account.",
        "Can you help me with a partnership inquiry?",
        "I need an invoice for my purchase.",
    ],
}


def weighted_choice(rng: np.random.Generator, weights: dict[str, float], size: int) -> np.ndarray:
    """Return ``size`` draws from a dict of {value: probability}."""
    keys = list(weights)
    probs = np.array([weights[k] for k in keys], dtype=float)
    probs = probs / probs.sum()
    return rng.choice(keys, size=size, p=probs)


def generate_orders(rng: np.random.Generator) -> list[dict]:
    """Build the order history and per-customer lifetime value."""
    customers = [f"customer{i:04d}@example.com" for i in range(N_CUSTOMERS)]
    cust_idx = rng.integers(0, N_CUSTOMERS, size=N_ORDERS)
    families = weighted_choice(rng, {name: w for name, w, _a, _m in FAMILIES}, N_ORDERS)

    family_params = {name: (params, months) for name, _w, params, months in FAMILIES}
    amounts = np.empty(N_ORDERS)
    warranty_months = np.empty(N_ORDERS, dtype=int)
    for i, family in enumerate(families):
        (mean, sigma), months = family_params[family]
        amounts[i] = rng.lognormal(np.log(mean), sigma)
        warranty_months[i] = months
    amounts = np.round(amounts, 2)

    days_ago = rng.integers(1, 731, size=N_ORDERS)

    ltv_by_customer: dict[int, float] = {}
    for i in range(N_ORDERS):
        ltv_by_customer[cust_idx[i]] = ltv_by_customer.get(cust_idx[i], 0.0) + float(amounts[i])

    orders = []
    for i in range(N_ORDERS):
        cidx = int(cust_idx[i])
        orders.append(
            {
                "order_id": f"ORD-{i + 1:05d}",
                "customer_email": customers[cidx],
                "order_date": (MONTH_START - timedelta(days=int(days_ago[i]))).date().isoformat(),
                "amount": f"{amounts[i]:.2f}",
                "product_family": families[i],
                "warranty_months": int(warranty_months[i]),
                "lifetime_value": f"{ltv_by_customer[cidx]:.2f}",
            }
        )
    return orders


def generate_requests(rng: np.random.Generator, orders: list[dict]) -> list[dict]:
    """Build the one-month baseline request set, joined to the order history."""
    orders_by_customer: dict[str, list[dict]] = {}
    for order in orders:
        orders_by_customer.setdefault(order["customer_email"], []).append(order)
    customers_with_orders = sorted(orders_by_customer)

    channels = weighted_choice(rng, CHANNEL_WEIGHTS, N_REQUESTS)
    topics = weighted_choice(rng, TOPIC_WEIGHTS, N_REQUESTS)
    seconds = rng.integers(0, MONTH_DAYS * 86400, size=N_REQUESTS)

    requests = []
    for i in range(N_REQUESTS):
        topic = str(topics[i])
        has_order = bool(rng.random() >= PROSPECT_SHARE)
        if has_order:
            email = customers_with_orders[int(rng.integers(0, len(customers_with_orders)))]
            order = orders_by_customer[email][int(rng.integers(0, len(orders_by_customer[email])))]
            order_id = order["order_id"]
            order_date = order["order_date"]
            warranty_months = order["warranty_months"]
            ltv = order["lifetime_value"]
        else:
            email = f"prospect{i:04d}@example.com"
            order_id = ""
            order_date = ""
            warranty_months = ""
            ltv = ""

        text = TEXTS[topic][int(rng.integers(0, len(TEXTS[topic])))]
        requests.append(
            {
                "request_id": f"REQ-{i + 1:05d}",
                "created_at": (MONTH_START + timedelta(seconds=int(seconds[i]))).isoformat(),
                "customer_email": email,
                "channel": str(channels[i]),
                "topic": topic,
                "request_text": text,
                "baseline_agent": f"agent{i % N_AGENTS + 1:02d}",
                "order_id": order_id,
                "order_date": order_date,
                "warranty_months": warranty_months,
                "lifetime_value": ltv,
            }
        )
    return requests


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    random.seed(SEED)  # keep stdlib consumers deterministic too

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    orders = generate_orders(rng)
    requests = generate_requests(rng, orders)

    write_csv(
        DATA_DIR / "orders.csv",
        orders,
        ["order_id", "customer_email", "order_date", "amount", "product_family", "warranty_months", "lifetime_value"],
    )
    write_csv(
        DATA_DIR / "requests_baseline.csv",
        requests,
        [
            "request_id",
            "created_at",
            "customer_email",
            "channel",
            "topic",
            "request_text",
            "baseline_agent",
            "order_id",
            "order_date",
            "warranty_months",
            "lifetime_value",
        ],
    )

    six = {"Order Status", "Return", "Warranty", "Shipping", "Sizing", "Store Hours"}
    six_share = 100.0 * sum(1 for r in requests if r["topic"] in six) / len(requests)
    matched = sum(1 for r in requests if r["order_id"])
    print(f"orders.csv             : {len(orders)} orders / {N_CUSTOMERS} customers")
    print(f"requests_baseline.csv  : {len(requests)} requests over {MONTH_DAYS} days")
    print(f"six recurring topics   : {six_share:.1f}% of volume")
    print(f"requests with an order : {100.0 * matched / len(requests):.1f}%")


if __name__ == "__main__":
    main()
