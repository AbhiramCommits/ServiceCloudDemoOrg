# ServiceCloudDemoOrg

An end-to-end **Solution Engineering proof of concept** for a fictional mid-market customer,
**Northwind Outfitters**. It takes the customer's stated support problem through the full SE loop —
discovery brief → deployable Salesforce org metadata → Apex/SOQL → a case-deflection assistant
(simulated in `sim/` — Agentforce is not provisioned in the Developer org) → a five-minute demo with
quantified before/after results. It ships two things that stay in
lockstep: **real Salesforce DX source-format metadata** you can deploy to an org, and a **Python
simulation harness** that implements the same business rules against synthetic data so every number in
this README is produced by actually running code in this repo, with no org and no internet required.

---

## 1. The business problem

Northwind is a B2C outdoor gear retailer: 280 employees, ~4,000 support cases/month, 12 agents, Sales
Cloud only. Support runs on a shared Gmail inbox plus a spreadsheet. Discovery named five pains:

| ID | Pain | Stated business impact | Owner |
| --- | --- | --- | --- |
| **P1** | No single case record — duplicate work across the inbox and the spreadsheet. | ~42 hours/week of re-typing and searching ≈ **$83K/year** | Marcus Bell (Team Lead) |
| **P2** | No priority or SLA routing — high-value customers wait as long as everyone else. | ~8 high-LTV customers lost/year ≈ **$34K/year at risk** | Dana Whitfield (VP CX) |
| **P3** | Agents answer the same ~6 questions repeatedly; no self-service deflection. | ~2,480 cases/month at ~11 min each ≈ **$228K/year** | Marcus Bell (Team Lead) |
| **P4** | Zero visibility — no real-time backlog, first-response time, or agent load. | ~6 hrs/week of manual reporting ≈ **$12K/year** | Dana Whitfield (VP CX) |
| **P5** | Warranty/entitlement eligibility checked manually against order history. | ~720 requests/month × ~3.5 min ≈ **$21K/year** | Riya Anand (Senior Agent) |

Full detail, the org chart and the 13 discovery questions are in [`docs/discovery-brief.md`](docs/discovery-brief.md).

---

## 2. Architecture

**Dual-track by design.** The `force-app/` tree is real deployable SFDX metadata. The `sim/` harness
re-implements the *same* constants and rules in Python — the priority weights, the SLA matrix, the
warranty date logic — so the before/after results are reproducible without a live org. A test
(`tests/test_metadata.py::test_apex_and_python_sla_matrix_agree`) fails the build if the Apex and
Python SLA matrices ever drift apart.

```
                          discovery brief ─────────────┐
                                                        │
   ┌───────────────────── Salesforce DX (deployable) ───┴─────────────────────┐
   │                                                                          │
   │  Support_Request__c  ──▶ SupportRequestTrigger ──▶ SupportRequestTriggerHandler
   │  Order_Record__c          (before insert/update, bulk-safe, 1 query/batch)
   │  Deflection_Article__c         │
   │                                ├── PriorityRouter.cls   (score + SLA + load balance)
   │                                └── WarrantyService.cls  (entitlement date math)
   │                                                                          │
   │  Flows: Support_Request_Triage · Warranty_Eligibility_Check · Case_Escalation_Alert
   │  Apex : SupportMetricsService · DeflectionAgentActions · tests
   │  UI   : Support_Console app · Support_Console_Record_Page · Support_Agent permission set
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      │  same rules, same constants
   ┌──────────────────────────────────┴───────────────────────────────────────┐
   │  Python harness (runnable, no org)                                        │
   │                                                                          │
   │  data/generate_data.py ─▶ orders.csv + requests_baseline.csv             │
   │        │                                                                 │
   │        ├─▶ sim/priority_router.py ─┐                                     │
   │        ├─▶ sim/warranty.py ────────┤─▶ sim/run_simulation.py ─▶ results/metrics.json
   │        ├─▶ sim/assistant.py ───────┘                                     │
   │        └─▶ sim/eval_assistant.py ─▶ results/assistant_eval.json          │
   │                    ▲                                                     │
   │  sim/config.py ────┘ (single source of truth: weights, SLA matrix, agent model)
   └──────────────────────────────────────────────────────────────────────────┘
```

### Repository layout

| Path | What it is |
| --- | --- |
| `force-app/main/default/objects/` | `Support_Request__c`, `Order_Record__c`, `Deflection_Article__c` — objects + fields with pain-tagged descriptions |
| `force-app/main/default/flows/` | `Support_Request_Triage` (record-triggered, P2), `Warranty_Eligibility_Check` (P5), `Case_Escalation_Alert` (P2/P4) |
| `force-app/main/default/classes/` | `PriorityRouter`, `WarrantyService`, `SupportMetricsService`, `SupportRequestTriggerHandler`, `DeflectionAgentActions` + two test classes |
| `force-app/main/default/triggers/` | `SupportRequestTrigger` (thin dispatcher, bulk-safe) |
| `force-app/main/default/flexipages/` | `Support_Console_Record_Page` (highlights panel, priority/SLA, related order, deflection region) |
| `force-app/main/default/applications/` | `Support_Console` Lightning app (Support Requests, Orders, Deflection Articles, dashboard tab) |
| `force-app/main/default/permissionsets/` | `Support_Agent` — object/field/Apex/tab access, read-only on commercial data |
| `force-app/main/default/tabs/` | Custom object tabs used by the app |
| `agentforce/` | Deflection agent spec (`deflection-agent.md`) and invocable-action map (`actions.md`) |
| `sim/` | Python harness: `config`, `priority_router`, `warranty`, `metrics`, `assistant`, `intents`, `run_simulation`, `eval_assistant` |
| `data/` | `generate_data.py` + generated `orders.csv`, `requests_baseline.csv`, `intent_eval.csv` |
| `docs/` | Discovery brief, SOQL reports, requirements traceability, demo script, slide outline, value model |
| `results/` | Generated artifacts committed for review: `metrics.json/.md`, `assistant_eval.json`, `confusion_matrix.md`, `deflection_by_topic.csv`, `requests_scored.csv` |
| `tests/` | 55 pytest tests across routing, warranty, metrics, assistant, metadata and the simulation |
| `.github/workflows/ci.yml` | CI: Python 3.11, run the pipeline, run pytest, validate all metadata XML |

---

## 3. How to run

### Local pipeline (no Salesforce org required)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python data/generate_data.py                       # deterministic synthetic data (seed 42)
python -m sim.run_simulation --out results/        # BASELINE vs SALESFORCE -> results/metrics.json
python -m sim.eval_assistant --out results/        # assistant eval -> results/assistant_eval.json
pytest -q                                          # 55 tests
```

Or run everything from clean in one step:

```bash
make all
```

(`make data`, `make sim`, `make eval`, `make test` are also available.)

### Deploying the Salesforce metadata

This requires a real org and an authenticated Dev Hub — it is not needed to reproduce any number in
this README.

```bash
sf org create scratch -f config/project-scratch-def.json -a demo
sf project deploy start -o demo
sf org open -o demo
```

---

## 4. Results

All figures below are copied from the committed `results/` artifacts produced by this build on a
synthetic Northwind-scale dataset.

**Dataset:** 3,000 orders / 1,200 customers · 4,000 support requests over 30 days · 12 agents ·
21 working days · 140 labelled evaluation utterances. `results/metrics.json`.

### Before / after — the five discovery metrics

| Metric | Baseline (today's process) | Salesforce | Δ | Δ% | Better |
| --- | ---: | ---: | ---: | ---: | --- |
| First response time — mean | 575.83 min (9.60 h) | 80.54 min (1.34 h) | −495.29 min | −86.0% | lower |
| First response time — p90 | 1,293.65 min (21.56 h) | 241.24 min (4.02 h) | −1,052.41 min | −81.3% | lower |
| SLA compliance | 43.15% | 97.30% | +54.15 pts | +125.5% | higher |
| Deflection rate | 0.00% | 56.95% | +56.95 pts | — | higher |
| Human-handled cases per agent per day | 15.87 | 6.83 | −9.04 | −57.0% | lower |
| Backlog age | 33.81 h | 3.10 h | −30.71 h | −90.8% | lower |

Supporting diagnostics (`results/metrics.json` → `diagnostics`):

| Diagnostic | Baseline | Salesforce |
| --- | ---: | ---: |
| Human-handled requests / month | 4,000 | 1,722 |
| Deflected requests / month | 0 | 2,278 |
| SLA breaches / month | 2,274 | 108 |
| Agent-load Gini | 0.000667 | 0.001742 |
| Agent-hours freed / month | — | **592.58** |

> The discovery brief recorded Northwind's *informal* SLA estimate as ~41% and its first-response
> estimate as ~9.4 h. The measured baseline lands at 43.15% and 9.60 h — close enough that the
> customer's instinct was right, and now it is measured rather than guessed.

### Deflection assistant (`results/assistant_eval.json`, `results/confusion_matrix.md`)

| Measure | Value |
| --- | ---: |
| Chosen confidence threshold | **0.55** |
| Overall intent accuracy | **97.86%** (137/140) |
| Macro F1 | 0.9787 |
| Escalation precision | **90.48%** |
| Escalation recall | 95.00% |
| Deflection rate at the chosen threshold (eval set) | 85.00% |

Per-intent F1 (support in parentheses):

| Intent | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Order Status | 1.0000 | 0.9500 | 0.9744 | 20 |
| Return | 1.0000 | 1.0000 | 1.0000 | 20 |
| Warranty | 1.0000 | 0.9500 | 0.9744 | 20 |
| Shipping | 1.0000 | 1.0000 | 1.0000 | 20 |
| Sizing | 1.0000 | 1.0000 | 1.0000 | 20 |
| Store Hours | 0.9524 | 1.0000 | 0.9756 | 20 |
| escalate (out of scope) | 0.9048 | 0.9500 | 0.9268 | 20 |

The `escalate` row is the guardrail: one out-of-scope request was answered as Store Hours
("Do you have any jobs open in your warehouse?"), and one in-scope request from each of Order Status
and Warranty was escalated rather than answered. The threshold sweep behind the 0.55 operating point
(6 thresholds, 0.40–0.65) is recorded in `results/assistant_eval.json` → `threshold_sweep`.

### Tests

```
55 passed in ~3.1s
```

(`pytest -q`, Python 3.11, pandas 3.0.6 / numpy 2.4.6.) The suite includes a metadata guard that
parses every `*-meta.xml`, checks every Apex class has a `-meta.xml`, fails on any SOQL query inside a
for-loop, verifies the Apex and Python SLA matrices agree, and asserts no `TODO` remains in the
traceability table.

### Annualized business value (`docs/value-model.md`)

| Component | Monthly | Annual |
| --- | ---: | ---: |
| Agent time released by deflection (592.58 h × $38/h loaded) | $22,518.04 | **$270,216.48** |
| SLA breaches avoided | 2,166 | 25,992 (not priced) |
| Human-handled load reduction | 9.04 cases/agent/day | — |

The $270,216.48 is the single headline dollar figure: 2,278 deflected requests/month × the baseline
15.18 handling minutes each, valued at the configured $38/hour loaded agent cost. Assumptions are
stated in `docs/value-model.md`.

---

## 5. Demo

| Artifact | What it is for |
| --- | --- |
| [`docs/demo-script.md`](docs/demo-script.md) | Timed 5-minute demo script — what to click, what to say, the pain ID each beat resolves, and the objection to expect — plus a 7-item technical objection-handling appendix. |
| [`docs/slide-outline.md`](docs/slide-outline.md) | 10-slide Google Slides outline; slide 10 carries the real simulation numbers. |
| [`docs/discovery-brief.md`](docs/discovery-brief.md) | The discovery artifact: current state, 13 questions, five named pains, success metrics and stakeholder map. |
| [`docs/requirements-traceability.md`](docs/requirements-traceability.md) | Pain → requirement → capability → repo path → metric moved, with every metric traced to `results/metrics.json`. |
| [`docs/soql-reports.md`](docs/soql-reports.md) | Five named SOQL reporting queries with the business question each answers. |
| [`docs/value-model.md`](docs/value-model.md) | The arithmetic from simulation metrics to annualized value, assumptions stated. |

---

## 6. Limitations & next steps

Honest scope of what this is and is not:

- **The data is synthetic.** `data/generate_data.py` produces a Northwind-scale dataset from a fixed
  seed. It is realistic in shape (six recurring topics ≈ 61% of volume, realistic order/LTV
  distribution) but it is not Northwind's real traffic.
- **What actually ran in Salesforce.** The metadata deploys cleanly to a Developer Edition
  (51 components, 0 errors) and the Apex suite passes there: 17/17 tests, 86-100% coverage per class
  (`results/apex/`). Priority scoring and warranty logic were executed in the org and match `sim/`
  exactly (`results/org_vs_sim.md`).
- **What did not run in Salesforce.** The org's release (Winter '27 Patch 8.6) never publishes
  API-created custom fields, so seeded records, the intake trigger, the Flows and the deflection
  actions could not be exercised end to end (`results/org_blocker.md`). The demo is driven by `sim/`,
  not by the org.
- **Agentforce and Einstein are not available here.** The Developer org exposes no `GenAiFunction`,
  `GenAiPlugin`, `GenAiPlanner` or Prompt Builder (`PromptTemplate`) entities, so this build has no
  Salesforce agent, prompt, or LLM. The "assistant" is the Python keyword/token-overlap router in
  `sim/assistant.py`. The org-side equivalents are the Flows and the `@InvocableMethod` wrapper
  classes (one action per class); they are deployed but were not run against data.
- **The assistant is a keyword/token-overlap intent router, not an LLM.** It is grounded (order status
  and warranty read `orders.csv`; policy answers come from approved content) and it escalates instead
  of guessing, but real language-model grounding and an Agentforce trust layer are out of scope. Its
  97.86% accuracy is on an in-vocabulary hand-written set and would fall on messier real traffic.
- **The "Salesforce" scenario is a model, not a deployment.** Response times are drawn from documented
  per-priority-band distributions (`sim/config.py`), not observed from a running org, so the deltas
  are directional evidence for the *rules*, not a service-level guarantee.
- **No Data Cloud / email-to-case / Shopify ingestion.** Moving data off the shared inbox and the
  store admin, and any history migration, are explicitly out of scope.
- **Value is modelled, not audited.** The $270K is arithmetic on measured simulated hours at a stated
  hourly cost; it excludes retention/CSAT value (which the discovery brief estimated at $34K/yr at
  risk) because the harness does not model churn.

**Next steps:** a two-week live pilot on one topic (Warranty, given its order-data grounding), wiring
`email-to-case` and a stopgap order feed, then replacing the simulator's parameters with observed
production distributions and re-scoring the same five metrics against this file.

---

## Reproducing this build

```bash
make all      # clean → generate data → simulate → evaluate → test
```

Deterministic: re-running regenerates byte-identical `results/` artifacts (verified by the git working
tree staying clean after `make all`).
