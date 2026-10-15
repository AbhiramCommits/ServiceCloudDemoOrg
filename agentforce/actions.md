# Deflection Agent — Invocable Actions

The six actions the agent can take. In a live org each is an `@InvocableMethod` in
`force-app/main/default/classes/DeflectionAgentActions.cls`, so it can be wired into an Agentforce
action, a Flow, or a `@wire`-driven Lightning component without further Apex. The local harness
(`sim/assistant.py`) implements the same actions against `data/orders.csv`.

| Action | Apex entry point | Backed by | Returns |
| --- | --- | --- | --- |
| `CheckOrderStatus` | `DeflectionAgentActions.checkOrderStatus` | SOQL on `Order_Record__c` (latest order by email) | Order id, order date, shipment stage |
| `StartReturn` | `DeflectionAgentActions.startReturn` | 30-day return policy + related order | Return confirmation text + reference order |
| `GetSizingGuide` | `DeflectionAgentActions.getSizingGuide` | `Deflection_Article__c` where `Topic__c = 'Sizing'` | Approved sizing guidance |
| `GetShippingPolicy` | `DeflectionAgentActions.getShippingPolicy` | `Deflection_Article__c` where `Topic__c = 'Shipping'` | Approved shipping options and timeframes |
| `CheckWarranty` | `DeflectionAgentActions.checkWarranty` | `WarrantyService.isUnderWarranty` over `Order_Record__c` | Coverage verdict + expiry date |
| `GetStoreHours` | `DeflectionAgentActions.getStoreHours` | `Deflection_Article__c` where `Topic__c = 'Store Hours'` | Store hours / locator guidance |

## Supporting Flows

* `Warranty_Eligibility_Check.flow-meta.xml` — auto-launched flow wrapping the same date logic, for
  declarative (no-code) callers.
* `Support_Request_Triage.flow-meta.xml` — scores and routes the request if the agent escalates.

## Escalation action

`DeflectionAgentActions.escalateToHuman` is not an intent of its own — it is the fallback the agent
returns when the router confidence is below the threshold, the intent is out of scope, or the
customer has no order on file. It leaves the request for `PriorityRouter` to route.

## Contract

Every action takes a bulk `List<AgentRequest>` and returns a parallel `List<AgentResponse>`, so a
single invocation can resolve a batch without per-row SOQL (the same bulk-safety rule the rest of the
Apex layer follows).
