# Org vs sim/ - logic comparison

Org values come from executing the deployed Apex (`PriorityRouter`, `WarrantyService`) via anonymous Apex.
Sim values come from `sim/priority_router.py` and `sim/warranty.py` with identical inputs.

> Seeded-record comparison (intake trigger, deflection actions) is blocked: this Salesforce release does not
> publish API-created custom fields (see `results/org_blocker.md`). Priority/warranty are pure logic, so they run.

## Priority routing

| Case | LTV | Channel | Topic | Org score | Sim score | Org band | Sim band | Org SLA | Sim SLA | Match |
|---|---|---|---|---|---|---|---|---|---|---|
| REQ-1 | 2500 | Phone | Warranty | 85 | 85 | Critical | Critical | 15m | 15m | yes |
| REQ-2 | 1200 | Chat | Return | 65 | 65 | High | High | 60m | 60m | yes |
| REQ-3 | 600 | Web | Shipping | 40 | 40 | Medium | Medium | 180m | 180m | yes |
| REQ-4 | 150 | Email | Sizing | 20 | 20 | Low | Low | 480m | 480m | yes |
| REQ-5 | 0 | Email | Other | 13 | 13 | Minimal | Minimal | 1440m | 1440m | yes |
| REQ-6 | 2500 | Email | Order Status | 60 | 60 | High | High | 60m | 60m | yes |
| REQ-7 | 1200 | Phone | Store Hours | 50 | 50 | High | High | 60m | 60m | yes |

## Warranty eligibility

| Check | Org | Sim | Match |
|---|---|---|---|
| alice_covered | True | True | yes |
| bob_boundary | True | True | yes |
| bob_day_after | False | False | yes |
| carol_expired | False | False | yes |
| zero_months | False | False | yes |
| null_date | False | False | yes |

## Differences

- No logic differences: scores, bands, SLA minutes and warranty verdicts match exactly on all cases.
- Message wording is identical except the date format: org `6/1/2026` vs sim `2026-06-01` (locale formatting).
- Not compared: intake trigger stamping, deflection actions, metrics. All require the custom fields that this org cannot publish.
