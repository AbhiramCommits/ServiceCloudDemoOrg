# ServiceCloudDemoOrg

Northwind Outfitters is a fictional 280-person outdoor retailer whose support team runs on a shared
inbox and a spreadsheet. This proof of concept turns its five discovery pains into deployable
Salesforce DX metadata — three custom objects, Apex routing/warranty/metrics, three Flows, a console
app and permission set — plus a Python harness that reproduces the same rules on synthetic data.
The metadata deploys to a Developer Edition; the before/after numbers come from the harness.

**Environment:** macOS 27 (arm64), Python 3.14, Salesforce CLI 2.154.4, Developer Edition on Winter '27.

---

## Results

### Simulated (`results/metrics.json`, `results/assistant_eval.json`)

Dataset: 3,000 orders, 4,000 requests, 12 agents, 21 working days, seed 42. Assistant evaluation:
140 labelled utterances.

| Metric | Baseline | Salesforce | Δ | Δ% |
| --- | ---: | ---: | ---: | ---: |
| First response time — mean | 575.83 min | 80.54 min | −495.29 min | −86.01% |
| First response time — p90 | 1,293.65 min | 241.24 min | −1,052.41 min | −81.35% |
| SLA compliance | 43.15% | 97.30% | +54.15 pts | +125.49% |
| Deflection rate | 0.00% | 56.95% | +56.95 pts | — |
| Human-handled cases per agent per day | 15.87 | 6.83 | −9.04 | −56.96% |
| Backlog age | 33.81 h | 3.10 h | −30.71 h | −90.83% |

| Diagnostic | Baseline | Salesforce |
| --- | ---: | ---: |
| Human-handled requests / month | 4,000 | 1,722 |
| Deflected requests / month | 0 | 2,278 |
| SLA breaches / month | 2,274 | 108 |
| Agent-load Gini | 0.000667 | 0.001742 |
| Agent-hours freed / month | — | 592.58 |

| Assistant measure | Value |
| --- | ---: |
| Chosen confidence threshold | 0.55 |
| Intent accuracy | 97.86% |
| Macro F1 | 0.9787 |
| Escalation precision | 90.48% |
| Escalation recall | 95.00% |
| Deflection rate (eval set) | 85.00% |

### Deployed and tested in a real org (`results/apex/`, `results/org_vs_sim.md`)

| Check | Result |
| --- | ---: |
| Apex tests in the org | 17/17 passing |
| Coverage per class | 86–100% |
| Priority cases matching the harness | 7/7 |
| Warranty checks matching the harness | 6/6 |

The org run executes the deployed `PriorityRouter` and `WarrantyService`; scores, bands, SLA minutes
and warranty verdicts match `sim/`. Seeded records, the intake trigger, the Flows and the deflection
actions were not run.

---

## What was validated vs. not validated

**Validated**

- Metadata deploys to a Developer Edition with no component errors.
- The Apex suite passes in the org; every class is above 75% coverage.
- Priority scoring and warranty eligibility match the Python harness on identical inputs.
- The Python pipeline, evaluation and pytest suite run from a clean checkout.

**Not validated**

- No seeded records, trigger execution, Flow execution or org-side metrics. The org's release does not
  publish API-created custom fields (`results/org_blocker.md`).
- No Agentforce, Einstein or Prompt Builder: the org exposes no `GenAiFunction`/`GenAiPlugin`/
  `GenAiPlanner`/`PromptTemplate` entities. The assistant is `sim/assistant.py`, not an org agent.
- No production traffic. Every delta is synthetic.

---

## How to run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python data/generate_data.py
python -m sim.run_simulation --out results/
python -m sim.eval_assistant --out results/
pytest -q
```

Salesforce side:

```bash
sf project deploy start -o <org>
sf apex run test -o <org> --test-level RunLocalTests --code-coverage
```

`make all` runs the full local pipeline. The org deploy needs an authenticated org; it is not needed
to reproduce any simulated number.

---

## Limitations

- The data is synthetic: realistic in shape, not Northwind's real traffic.
- The "Salesforce" side of the before/after is a model (`sim/config.py`), not observed service levels.
- The assistant is a keyword/token-overlap router, not an LLM. Its accuracy is measured on an
  in-vocabulary set and would drop on messier traffic.
- The org cannot be seeded on this Salesforce release; the Flows and invocable wrappers are deployed
  but have not run against data.
- No Data Cloud, email-to-case or order-feed ingestion; no history migration.
- Value is modelled from simulated hours, not audited.

---

## What I learned

- TODO
- TODO
- TODO
