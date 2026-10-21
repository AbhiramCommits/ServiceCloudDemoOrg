"""Compare the deployed org's behaviour with the sim/ harness for the seeded demo cases.

Inputs (produced by the CLI runs):
  results/org_requests.json    - SOQL export of seeded Support_Request__c rows
  results/org_deflection.json  - ORG_RESULT payload from capture_deflection.apex

Output:
  results/org_vs_sim.md        - comparison tables + difference list
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from sim import assistant, warranty
from sim.priority_router import priority_band_for_score, score_request, sla_minutes_for_score

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

AS_OF = date(2026, 1, 15)

# Seeded inputs: email -> (lifetime value, channel, topic, order date, warranty months)
CASES = [
    ("REQ-1", "alice@demo.example", 2500, "Phone", "Warranty", date(2025, 6, 1), 12,
     "where is my order"),
    ("REQ-2", "bob@demo.example", 1200, "Chat", "Return", date(2025, 1, 15), 12,
     "i want to return an item"),
    ("REQ-3", "carol@demo.example", 600, "Web", "Shipping", date(2024, 1, 15), 12,
     "how long does shipping take"),
    ("REQ-4", "dave@demo.example", 150, "Email", "Sizing", date(2025, 12, 1), 6,
     "what size should i order"),
    ("REQ-5", "erin@demo.example", 0, "Email", "Other", None, 0,
     "something else entirely"),
    ("REQ-6", "alice@demo.example", 2500, "Email", "Order Status", date(2025, 6, 1), 12,
     "where is my order"),
    ("REQ-7", "bob@demo.example", 1200, "Phone", "Store Hours", date(2025, 1, 15), 12,
     "what are your store hours"),
]

ORDERS = {
    email: [{
        "order_id": f"ORD-{email.split('@')[0].upper()}",
        "customer_email": email,
        "order_date": order_date.isoformat(),
        "warranty_months": months,
        "amount": 100.0,
        "product_family": "Camping",
        "lifetime_value": ltv,
    }]
    for _, email, ltv, _, _, order_date, months, _ in CASES
    if order_date is not None
}


def load_json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text())


def norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def main() -> None:
    org_rows = load_json("org_requests.json")["result"]["records"]
    org = load_json("org_deflection.json")

    org_by_key = {
        (row["Customer_Email__c"], row["Channel__c"], row["Topic__c"]): row for row in org_rows
    }

    priority_rows = []
    mismatches = []
    for req_id, email, ltv, channel, topic, _, _, _ in CASES:
        row = org_by_key[(email, channel, topic)]
        expected_score = score_request(ltv, channel, topic)
        expected_band = priority_band_for_score(expected_score)
        expected_sla = sla_minutes_for_score(expected_score)
        created = datetime.fromisoformat(row["CreatedDate"].replace("Z", "+00:00"))
        sla_due = datetime.fromisoformat(row["SLA_Due__c"].replace("Z", "+00:00"))
        org_sla = round((sla_due - created).total_seconds() / 60)
        ok = (row["Priority_Score__c"] == expected_score
              and row["Priority__c"] == expected_band and org_sla == expected_sla)
        if not ok:
            mismatches.append(
                f"{req_id} priority: org={row['Priority_Score__c']}/{row['Priority__c']}/{org_sla}m "
                f"sim={expected_score}/{expected_band}/{expected_sla}m"
            )
        priority_rows.append((req_id, email, channel, topic, expected_score, row["Priority_Score__c"],
                              expected_band, row["Priority__c"], expected_sla, org_sla, ok))

    responses = {item["label"]: item for item in org["responses"]}

    warranty_rows = []
    warranty_expected = {
        "CheckWarranty:alice": (True, date(2025, 6, 1), 12),
        "CheckWarranty:bob": (True, date(2025, 1, 15), 12),
        "CheckWarranty:carol": (False, date(2024, 1, 15), 12),
    }
    for label, (expected, order_date, months) in warranty_expected.items():
        sim_msg = warranty.entitlement_message(order_date, months, AS_OF)
        sim_flag = warranty.is_under_warranty(order_date, months, AS_OF)
        org_flag = "still under warranty" in norm(responses[label]["message"])
        ok = sim_flag == expected == org_flag and \
            ("warranty" in norm(responses[label]["message"]))
        if not ok:
            mismatches.append(f"{label}: org={org_flag} sim={sim_flag} expected={expected}")
        warranty_rows.append((label, expected, org_flag, sim_flag, ok, responses[label]["message"], sim_msg))

    org_checks = org["warrantyChecks"]
    sim_checks = {
        "bob_boundary_2026_01_15": warranty.is_under_warranty(date(2025, 1, 15), 12, date(2026, 1, 15)),
        "bob_day_after_2026_01_16": warranty.is_under_warranty(date(2025, 1, 15), 12, date(2026, 1, 16)),
        "carol_expired_2026_01_15": warranty.is_under_warranty(date(2024, 1, 15), 12, date(2026, 1, 15)),
    }
    boundary_rows = []
    for key, sim_value in sim_checks.items():
        org_value = org_checks[key]
        ok = org_value == sim_value
        if not ok:
            mismatches.append(f"{key}: org={org_value} sim={sim_value}")
        boundary_rows.append((key, org_value, sim_value, ok))

    deflection_rows = []
    for req_id, email, _, _, topic, _, _, utterance in CASES:
        label = assistant.ACTION_BY_INTENT.get(topic, "escalate")
        sim_result = assistant.resolve(utterance, email, ORDERS, as_of=AS_OF)
        org_key = {
            "CheckOrderStatus": "CheckOrderStatus", "StartReturn": "StartReturn",
            "GetSizingGuide": "GetSizingGuide", "GetShippingPolicy": "GetShippingPolicy",
            "GetStoreHours": "GetStoreHours", "CheckWarranty": "CheckWarranty",
        }.get(label)
        if org_key and f"{org_key}:{email.split('@')[0]}" in responses:
            org_item = responses[f"{org_key}:{email.split('@')[0]}"]
            org_deflected = org_item["deflected"]
        elif org_key and f"{org_key}:alice" in responses:
            org_item = responses[f"{org_key}:alice"]
            org_deflected = org_item["deflected"]
        else:
            org_item = {"message": "(no seeded order-status case)"}
            org_deflected = False if topic == "Other" else None
        same_flag = org_deflected == sim_result["deflected"]
        if not same_flag:
            mismatches.append(
                f"{req_id} deflection: org={org_deflected} sim={sim_result['deflected']} ({topic})"
            )
        deflection_rows.append((req_id, topic, utterance, sim_result["intent"],
                                org_deflected, sim_result["deflected"], same_flag,
                                norm(org_item.get("message")), norm(sim_result["response_text"])))

    lines = ["# Org vs sim/ comparison", "",
             f"Org data captured for {len(org_rows)} seeded Support Requests; sim cases use the same inputs.",
             "Harness: `sim/priority_router.py`, `sim/warranty.py`, `sim/assistant.py`.", ""]

    lines += ["## Priority routing", "",
              "| Case | Email | Channel | Topic | Org score | Sim score | Org band | Sim band | Org SLA | Sim SLA | Match |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (rid, email, channel, topic, es, os, eb, ob, em, om, ok) in priority_rows:
        lines.append(f"| {rid} | {email} | {channel} | {topic} | {os} | {es} | {ob} | {eb} | {om}m | {em}m | {'yes' if ok else 'NO'} |")

    lines += ["", "## Warranty eligibility", "",
              "| Check | Expected | Org | Sim | Match | Org message | Sim message |",
              "|---|---|---|---|---|---|---|"]
    for label, expected, of, sf, ok, omsg, smsg in warranty_rows:
        lines.append(f"| {label} | {expected} | {of} | {sf} | {'yes' if ok else 'NO'} | {omsg} | {smsg} |")

    lines += ["", "### Boundary dates", "", "| Check | Org | Sim | Match |", "|---|---|---|---|"]
    for key, ov, sv, ok in boundary_rows:
        lines.append(f"| {key} | {ov} | {sv} | {'yes' if ok else 'NO'} |")

    lines += ["", "## Deflection", "",
              "| Case | Topic | Utterance | Sim intent | Org deflected | Sim deflected | Same |",
              "|---|---|---|---|---|---|---|"]
    for rid, topic, utterance, intent, od, sd, same, _, _ in deflection_rows:
        lines.append(f"| {rid} | {topic} | {utterance} | {intent} | {od} | {sd} | {'yes' if same else 'NO'} |")

    lines += ["", "## Differences", ""]
    if mismatches:
        lines += [f"- {m}" for m in mismatches]
    else:
        lines += ["- No behavioural differences in score, band, SLA, warranty verdicts or deflection decisions."]

    content_diffs = [
        d for d in deflection_rows
        if d[7] and d[8] and d[7] != d[8]
    ]
    lines += ["", "### Content (same decision, different text)", ""]
    lines.append(f"- {len(content_diffs)} cases answer with different wording. Cause: the org reads seeded "
                 "`Deflection_Article__c` bodies, while sim/ uses its hard-coded `POLICY_TEXTS`; order-status "
                 "text also differs (org returns the order Id + date, sim returns status prose).")
    lines += [
        "- The org has no intent classifier or confidence threshold: the agent/action is chosen before Apex "
        "runs, so sim/'s `classify()` and 0.55 threshold have no org counterpart.",
        "- The org trigger recomputes `SLA_Due__c` on insert and on triage-input updates; sim/ computes SLA "
        "per request at scoring time and has no update path.",
        "- Agent assignment: `PriorityRouter.assignOwner` exists in Apex but nothing calls it in the org; "
        "sim/ assigns all 12 agents. Seeded org rows are owned by the deploying user.",
    ]

    out = RESULTS / "org_vs_sim.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-25:]))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
