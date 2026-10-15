# Deflection Agent — Northwind Support Assistant

> Agentforce-style agent definition. In a live org this maps to an Agentforce agent (or an Einstein
> bot) with these topics and actions; here it is the specification that `DeflectionAgentActions.cls`
> and `sim/assistant.py` both implement.

## Role

Answer the six recurring support questions Northwind's agents answer by hand today (pain P3) so the
human team spends its time on the work that actually needs a human, and so first-response time drops
for everyone (pain P2). The agent is a **front door**, not a replacement: it resolves what it can
ground in real order data, answers policy questions from approved content, and escalates everything
else.

## Topics (intents)

| Intent | What the customer is asking | Backing action | Grounded in |
| --- | --- | --- | --- |
| Order Status | Where is my order / has it shipped / what's the ETA | `CheckOrderStatus` | `Order_Record__c` (order date → shipment stage) |
| Return | How do I return / exchange / get a refund | `StartReturn` | 30-day return policy + related order |
| Sizing | What size should I order / how does it fit | `GetSizingGuide` | approved sizing content (`Deflection_Article__c`) |
| Shipping | How long / how much / do you ship to… | `GetShippingPolicy` | approved shipping content |
| Warranty | Is this covered / can it be repaired | `CheckWarranty` | `WarrantyService.isUnderWarranty` over order history |
| Store Hours | When are you open / where is the store | `GetStoreHours` | store locator content |

Anything that is not one of these six — billing, account access, loyalty, gift cards, corporate
accounts, complaints — is **out of scope** and must escalate.

## Guardrails

1. **Never invent order facts.** Order Status and Warranty answers are produced only from
   `Order_Record__c` rows joined on the customer's email. If no order matches, the agent escalates
   instead of guessing.
2. **Confidence threshold.** A request is only resolved when the router's confidence clears the
   operating point (0.55, chosen in `results/assistant_eval.json`). Below it, the agent escalates.
3. **Explicit escalate_to_human fallback.** Out-of-scope, low-confidence, and data-less requests all
   return a human handoff rather than an answer.
4. **No commitments the business has not approved.** Refunds, warranty verdicts and shipping
   promises come from policy data, not improvisation.
5. **No new personal data.** The agent reads the order history it is entitled to and writes nothing.

## Escalation

Escalated requests are handed to the queue and routed by `PriorityRouter` (priority score + SLA), so a
high-value warranty question still jumps ahead of a low-value one — the P2 behaviour, applied to the
work the assistant could not finish.

## Measured behaviour

`results/assistant_eval.json` (produced by `python -m sim.eval_assistant`) is the authority on this
agent's accuracy. The README reports its real overall accuracy, per-intent F1, escalation precision
and the deflection rate at the chosen threshold.
