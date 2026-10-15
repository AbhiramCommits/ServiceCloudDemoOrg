# Slide Outline — Northwind Outfitters Support PoC

10-slide Google Slides outline. One block per slide: **title**, **the single message**, **the
visual**, **the speaker note**. Slide 10 carries the real simulation output — do not edit its numbers
by hand; copy them from `results/metrics.json`.

---

## Slide 1 — "4,000 requests a month, and no one can see them"

- **Single message:** Northwind runs a modern retail business on a shared inbox and a spreadsheet.
- **Visual:** two panes — a Gmail inbox at 4pm with 400 unread, and `Case Log.xlsx` scrolled to the
  last-edited row ("4 hours behind"). Screenshot-style, no polish.
- **Speaker note:** Open with the customer's own words from discovery. Name the volume (4,000/month),
  the team (12 agents), and the fact that support is the last unmeasured part of the business.

## Slide 2 — "Five named pains, five owners"

- **Single message:** the problem is specific, costed, and someone owns each part of it.
- **Visual:** the P1–P5 table from `docs/discovery-brief.md` — pain, dollar/hours impact, owner.
- **Speaker note:** Read the impacts, not the descriptions. P3 is the biggest: ~$228K/year of agent
  time on six repeat questions. Land that this is not a technology problem, it is a queueing problem.

## Slide 3 — "The five numbers we will move"

- **Single message:** we agreed the scoreboard before we built anything.
- **Visual:** the success-metrics table with stated baselines (first response 9.4h, deflection 0%,
  SLA 41%, 16 cases/agent/day, 34h backlog).
- **Speaker note:** This is the contract for the demo. Everything after this slide is measured
  against these five. The last slide returns here.

## Slide 4 — "One record instead of two systems" (P1)

- **Single message:** every request becomes a Support Request record with its order attached.
- **Visual:** the Support Console record page — highlights panel, priority/SLA block, Related Order.
- **Speaker note:** Emphasise the order lookup: the agent never opens the store admin again. This
  single change kills both the duplicate work and the "did you take this?" problem.

## Slide 5 — "Priority and SLA, decided by rule not by feel" (P2)

- **Single message:** lifetime value, channel and topic set the score, and the score sets the clock.
- **Visual:** the scoring weights and the SLA matrix (15m / 1h / 3h / 8h / 24h), plus a side-by-side
  of a $60 buyer and a $4,200 customer scoring 5 vs 85.
- **Speaker note:** The whale now jumps the queue by rule. Mention `Case_Escalation_Alert` flags any
  request that passes its SLA with no first response.

## Slide 6 — "The assistant answers the six questions, and escalates the rest" (P3)

- **Single message:** grounded self-service for the repeat questions; a human handoff for everything
  else.
- **Visual:** the six intents and their action names, with a "confidence < 0.55 → escalate" guardrail
  callout, and a screenshot of a live order-status answer.
- **Speaker note:** Say the accuracy out loud (97.9% on 140 labelled utterances) and the escalation
  precision (91%). The point is that it *refuses* rather than guesses.

## Slide 7 — "Warranty eligibility, computed not counted on fingers" (P5)

- **Single message:** entitlement is a date calculation against order history, done automatically.
- **Visual:** the `Warranty_Eligibility_Check` flow logic — order date + warranty months vs request
  date, inclusive boundary — with a covered and an expired example.
- **Speaker note:** This removes ~7 minutes of tab-hopping from every warranty and return case and
  eliminates the boundary-case mistakes that were quietly costing return margin.

## Slide 8 — "Leadership sees the backlog live" (P4)

- **Single message:** the weekly hand-built spreadsheet becomes a real-time SOQL view.
- **Visual:** the dashboard mock with backlog by priority, first-response cohorts, SLA breaches by
  agent, and deflection by topic; annotate "5 named queries in `docs/soql-reports.md`".
- **Speaker note:** Marcus stops spending six hours a week rebuilding a stale roll-up. Backlog age is
  visible to the hour, per priority band.

## Slide 9 — "Same rules, deployed or simulated"

- **Single message:** the PoC is real deployable metadata **and** a reproducible harness.
- **Visual:** two-column diagram — left: `force-app/` SFDX metadata (objects, Flows, Apex,
  Lightning app, permission set); right: `sim/` Python harness implementing the same constants;
  a double arrow labelled "shared constants in `sim/config.py` and `PriorityRouter.cls`".
- **Speaker note:** This is the credibility slide for Tom. `sf project deploy start` ships the org;
  `make all` reproduces every number without an org. Neither can drift silently — a test fails if the
  Apex and Python SLA matrices disagree.

## Slide 10 — "The measured result" (real simulation output)

- **Single message:** on 4,000 requests, every headline metric moved, and the time released is worth
  $270,216 a year.
- **Visual:** the before/after table below, copied from `results/metrics.json` and
  `docs/value-model.md`, plus the assistant's real accuracy from `results/assistant_eval.json`.

| Metric | Baseline | Salesforce | Change |
| --- | ---: | ---: | ---: |
| First response — mean | 575.83 min (9.60 h) | 80.54 min (1.34 h) | −86.0% |
| First response — p90 | 1,293.65 min (21.56 h) | 241.24 min (4.02 h) | −81.3% |
| SLA compliance | 43.15% | 97.30% | +54.15 pts |
| Deflection rate | 0.00% | 56.95% | +56.95 pts |
| Human-handled cases / agent / day | 15.87 | 6.83 | −57.0% |
| Backlog age | 33.81 h | 3.10 h | −90.8% |
| Assistant accuracy (140 utterances) | — | 97.86% | — |
| Assistant escalation precision | — | 90.48% | — |
| Agent-hours freed / month | — | 592.58 h | — |
| Annualized value | — | **$270,216.48** | — |

- **Speaker note:** Pause on the $270K. Then the ask: a two-week pilot on one topic with Riya's team,
  comparing live numbers against this file. Do not add a number that is not in `results/`.

---

### Build note

Slides 4, 6, 8 and 10 depend on artifacts in this repo. Re-run `make all` before the demo and paste
the fresh `results/metrics.md` table into slide 10 so the deck can never be stale.
