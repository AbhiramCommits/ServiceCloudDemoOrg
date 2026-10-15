"""Local, runnable case-deflection assistant (the Agentforce-style component).

The router does three things:

1. **Intent routing** over the six recurring P3 topics using normalized keyword/regex signals plus
   token-overlap scoring against intent exemplars (:mod:`sim.intents`), with a confidence threshold.
2. **Escalation** - anything below the confidence threshold, below the minimum match score, or that
   needs order data the customer does not have, is explicitly routed to ``escalate_to_human`` rather
   than answered. The assistant is not allowed to guess.
3. **Grounded resolution** - order-status and warranty answers read the real order history
   (``data/orders.csv``) rather than inventing facts.

The same six actions are exposed to Salesforce by ``DeflectionAgentActions.cls``.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from . import intents as intent_mod
from . import warranty

#: Confidence at or above which a classified intent is acted on. Chosen in ``sim/eval_assistant.py``
#: by sweeping thresholds against the labelled evaluation set; see ``results/assistant_eval.json``.
DEFAULT_THRESHOLD = 0.55

#: Absolute match score below which the utterance is treated as out-of-scope even if it "wins".
MIN_SCORE = 1.5

#: Assistant intent -> invocable action name (mirrors agentforce/actions.md).
ACTION_BY_INTENT: dict[str, str] = {
    "Order Status": "CheckOrderStatus",
    "Return": "StartReturn",
    "Sizing": "GetSizingGuide",
    "Shipping": "GetShippingPolicy",
    "Warranty": "CheckWarranty",
    "Store Hours": "GetStoreHours",
}

#: Intents that cannot be answered without knowing the customer's order.
REQUIRES_ORDER: set[str] = {"Order Status", "Warranty"}

ESCALATION_TEXT = (
    "Let me connect you with a Northwind specialist who can help with that - "
    "one of our team will pick this up shortly."
)

POLICY_TEXTS = {
    "Sizing": (
        "Our gear runs true to size. Between sizes, size up for footwear and down for insulated "
        "jackets. Full size charts for every product are on the product page under 'Sizing'."
    ),
    "Shipping": (
        "Standard shipping is free over $75 and takes 3-5 business days; express is 1-2 business "
        "days. We ship across the US and to Canada. Tracking arrives by email when your order ships."
    ),
    "Store Hours": (
        "Our Bozeman flagship is open Monday-Saturday 9am-7pm and Sunday 10am-6pm. Store hours for "
        "every location are on the Store locator page."
    ),
}


def classify(text: str, threshold: float | None = None) -> tuple[str, float, dict[str, float]]:
    """Route ``text`` to one of the six intents or ``"escalate"``.

    Returns ``(intent, confidence, raw_scores)``. Confidence saturates as ``score / (score + 3)``,
    so a couple of strong signals are needed to clear the threshold.
    """
    threshold = DEFAULT_THRESHOLD if threshold is None else threshold
    scores = intent_mod.score_intents(text)
    best = max(scores, key=lambda k: scores[k])
    best_score = scores[best]
    confidence = round(best_score / (best_score + 1.5), 4) if best_score > 0 else 0.0

    if best_score < MIN_SCORE or confidence < threshold:
        return "escalate", confidence, scores
    return best, confidence, scores


def _order_date(order: dict) -> date | None:
    raw = order.get("order_date")
    if not raw:
        return None
    return datetime.fromisoformat(str(raw)).date()


def _order_status(order: dict, as_of: date) -> str:
    placed = _order_date(order)
    if placed is None:
        return "in our system"
    age_days = (as_of - placed).days
    if age_days <= 2:
        return "being packed at the warehouse"
    if age_days <= 9:
        return "in transit with the carrier"
    return "delivered"


def _latest_order(orders: list[dict]) -> dict | None:
    dated = [(o, _order_date(o)) for o in orders if _order_date(o) is not None]
    if not dated:
        return orders[0] if orders else None
    return max(dated, key=lambda pair: pair[1])[0]


def _respond(intent: str, orders: list[dict], as_of: date) -> str:
    order = _latest_order(orders)
    if intent == "Order Status":
        if order is None:
            return ESCALATION_TEXT
        return (
            f"Thanks for reaching out! Order {order['order_id']} was placed on "
            f"{order['order_date']} and is currently {_order_status(order, as_of)}."
        )
    if intent == "Warranty":
        if order is None:
            return ESCALATION_TEXT
        verdict = warranty.entitlement_message(
            order.get("order_date"), order.get("warranty_months"), as_of
        )
        return f"Checking order {order['order_id']}: {verdict}"
    if intent == "Return":
        reference = f"an order ({order['order_id']})" if order else "your order"
        return (
            f"You can start a return within 30 days of delivery on {reference}. "
            "I have opened a return and emailed you a prepaid label - "
            "drop it at any carrier location and your refund posts in 3-5 days."
        )
    return POLICY_TEXTS.get(intent, ESCALATION_TEXT)


def resolve(
    request_text: str,
    customer_email: str | None = None,
    order_lookup: dict[str, list[dict]] | None = None,
    threshold: float | None = None,
    as_of: date | None = None,
) -> dict:
    """Resolve one inbound request.

    Returns a dict with ``intent``, ``confidence``, ``action_taken``, ``deflected`` and
    ``response_text``. ``deflected`` is True only when the assistant answered without a human.
    """
    intent, confidence, _scores = classify(request_text, threshold)
    as_of_date = as_of or date.today()

    if intent == "escalate":
        return {
            "intent": "escalate",
            "confidence": confidence,
            "action_taken": "escalate_to_human",
            "deflected": False,
            "response_text": ESCALATION_TEXT,
        }

    orders = (order_lookup or {}).get((customer_email or "").lower(), [])
    if intent in REQUIRES_ORDER and not orders:
        return {
            "intent": intent,
            "confidence": confidence,
            "action_taken": "escalate_to_human",
            "deflected": False,
            "response_text": (
                "I could not find an order on your account, so I have asked a specialist "
                "to help you directly."
            ),
        }

    return {
        "intent": intent,
        "confidence": confidence,
        "action_taken": ACTION_BY_INTENT[intent],
        "deflected": True,
        "response_text": _respond(intent, orders, as_of_date),
    }


def load_order_lookup(orders_csv: str | Path) -> dict[str, list[dict]]:
    """Build an ``email -> [orders]`` lookup from ``data/orders.csv`` for grounded answers."""
    lookup: dict[str, list[dict]] = {}
    with Path(orders_csv).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lookup.setdefault(row["customer_email"].lower(), []).append(row)
    return lookup
