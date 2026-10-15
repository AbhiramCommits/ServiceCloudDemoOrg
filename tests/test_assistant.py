"""Tests for the deflection assistant: routing, escalation and grounded answers."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from sim import assistant

DATA = Path(__file__).resolve().parents[1] / "data"
ORDER_LOOKUP = assistant.load_order_lookup(DATA / "orders.csv")

CANONICAL = {
    "Order Status": "Where is my order? It has not arrived yet.",
    "Return": "I want to return these boots for a refund.",
    "Warranty": "Is my tent still under warranty? The pole snapped.",
    "Shipping": "How long does standard shipping take?",
    "Sizing": "What size jacket should I order if I am between medium and large?",
    "Store Hours": "What time do you open on Saturday?",
}


@pytest.mark.parametrize("intent,utterance", list(CANONICAL.items()))
def test_canonical_utterance_routes_to_its_intent(intent, utterance):
    predicted, confidence, _scores = assistant.classify(utterance)
    assert predicted == intent, f"{utterance!r} -> {predicted}"
    assert confidence >= assistant.DEFAULT_THRESHOLD


def test_out_of_scope_escalates():
    for utterance in [
        "Do you offer gift cards?",
        "I have a question about my loyalty points.",
        "Can you help me set up a corporate account?",
        "Please remove my personal data from your systems.",
    ]:
        assert assistant.classify(utterance)[0] == "escalate", utterance


def test_confidence_below_threshold_escalates():
    # An in-vocabulary utterance with an impossible threshold must escalate, not guess.
    assert assistant.classify(CANONICAL["Shipping"], threshold=0.99)[0] == "escalate"
    # A genuinely ambiguous utterance escalates at the default threshold.
    assert assistant.classify("It is a nice day outside.")[0] == "escalate"


def test_order_status_response_is_grounded_in_orders_csv():
    email = next(iter(ORDER_LOOKUP))
    orders = ORDER_LOOKUP[email]
    latest = max(orders, key=lambda o: o["order_date"])

    result = assistant.resolve(
        "Where is my order? It has not arrived yet.",
        customer_email=email,
        order_lookup=ORDER_LOOKUP,
        as_of=date.fromisoformat(latest["order_date"]),
    )
    assert result["intent"] == "Order Status"
    assert result["action_taken"] == "CheckOrderStatus"
    assert result["deflected"] is True
    assert latest["order_id"] in result["response_text"], "Response must cite the real order"


def test_warranty_response_uses_order_history():
    covered = None
    for email, orders in ORDER_LOOKUP.items():
        for order in orders:
            if int(order["warranty_months"]) >= 12:
                covered = (email, order)
                break
        if covered:
            break
    email, order = covered
    from datetime import datetime

    as_of = datetime.fromisoformat(order["order_date"]).date()
    result = assistant.resolve(
        "Is my order still under warranty?", customer_email=email, order_lookup=ORDER_LOOKUP, as_of=as_of
    )
    assert result["deflected"] is True
    assert "warranty" in result["response_text"].lower()


def test_escalates_when_customer_has_no_order():
    result = assistant.resolve(
        "Is my tent still under warranty?",
        customer_email="nobody@nowhere.example",
        order_lookup=ORDER_LOOKUP,
    )
    assert result["intent"] == "Warranty"
    assert result["deflected"] is False
    assert result["action_taken"] == "escalate_to_human"


def test_resolve_returns_full_contract():
    result = assistant.resolve(
        "What time do you open on Saturday?", customer_email="anyone@example.com", order_lookup={}
    )
    assert set(result) == {"intent", "confidence", "action_taken", "deflected", "response_text"}
    assert result["action_taken"] == "GetStoreHours"
    assert result["deflected"] is True
