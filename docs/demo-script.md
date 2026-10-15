# Northwind Outfitters — 5-Minute Demo Script

**Audience:** Dana Whitfield (VP CX), Marcus Bell (Support Team Lead), Tom Reyes (IT), one senior agent.
**Goal:** show that the five named pains are solved by working metadata, and close on measured numbers.
**Runtime:** 5:00. Rehearse to 4:45 so there is room for one interruption.

> Numbers in this script are the ones produced by this repo (`results/metrics.json`,
> `results/assistant_eval.json`). Do not say a number that is not in those files.

---

## 0:00 — Set the stage

- **What you click:** nothing. Slack/Teams is on screen; Salesforce is behind it.
- **What you say:** "Dana, when we did discovery you told me your team 'did a lot and finished
  nothing' — 4,000 requests a month through a shared inbox, a spreadsheet four hours behind, no
  priority, and no self-service. Marcus told me a whale customer waits behind a sizing question.
  Riya told me she answers the same six questions all day. I'm going to show you that same month,
  with those same 4,000 requests, run through Service Cloud — and I'll finish with the numbers."
- **Pain:** P1–P5 (framing).
- **Objection → response:** *"Is this a slideware mock-up?"* → "Every number I show you is produced by
  running the configuration in this repo; you can re-run it yourself and get the same file."

## 0:30 — "Today" screen

- **What you click:** a browser tab showing the shared inbox and `Case Log.xlsx` side by side; then
  the baseline row of `results/metrics.md`.
- **What you say:** "This is today. Two systems, no case record, no priority, no SLA. Read the
  baseline column: first response averages 575 minutes — nearly ten hours; only 43% of requests beat
  the SLA we would propose; the average piece of work sits open 34 hours; and zero percent is
  deflected because there is nothing to deflect to."
- **Pain:** P1, P4.
- **Objection → response:** *"Those baseline numbers are guesses."* → "They're simulated from your
  stated volume and the six-topic mix; the *definitions* match the metrics you'll report after
  go-live. The whole point is that today you can't measure them at all."

## 1:00 — Support Console walkthrough (P1)

- **What you click:** the **Support Console** Lightning app → **Support Requests** tab → open
  `SR-10000`. Point at the highlights panel, the priority/SLA block, and the Related Order region.
- **What you say:** "One record. Request number, customer, channel, topic, priority score, SLA due,
  first response, status, related order, CSAT. The order is *attached*, so the agent never opens
  another tab. This replaces the inbox and the spreadsheet in one move."
- **Pain:** **P1**.
- **Objection → response:** *"My agents won't adopt another tool."* → "It's one screen with fewer
  clicks than what they do now, and the console does the parts they hate — priority, SLA, warranty
  lookup. We onboard Riya as the champion, not the skeptic."

## 1:45 — Priority + SLA routing, and a whale jumps the queue (P2)

- **What you click:** create two requests via the console — one from a $60 first-time buyer
  (email, sizing) and one from a $4,200-LTV customer (phone, warranty). Show the triage result:
  priority score 5 vs 85, `Critical` vs `Minimal`, SLA due in 15 minutes vs 24 hours.
- **What you say:** "The record-triggered triage flow scores lifetime value, channel and topic, then
  stamps the SLA from the matrix — 15 minutes for critical, 24 hours for minimal. The whale is now
  impossible to miss. Two thousand two hundred seventy-four requests breached the SLA today; with
  routing that falls to one hundred and eight."
- **Pain:** **P2** (and it sets up P5 for the warranty case).
- **Objection → response:** *"Leaders will game the priority score."* → "It's explainable and
  version-controlled — three weighted inputs, in `PriorityRouter.cls`. If the weighting is wrong we
  change a constant, not a culture."

## 2:45 — Deflection agent answers live (P3 and P5)

- **What you click:** in the deflection region, run the assistant on *"Where is my order?"* → it
  returns the customer's real order and its stage. Then *"Is my tent still under warranty?"* → it
  returns the verdict from order history. Then run an out-of-scope request → watch it escalate.
- **What you say:** "The six questions your team answers by hand are routed by intent. Order status
  and warranty are *grounded* — they read the order record, they don't guess. Out-of-scope, low
  confidence, or no order on file escalates to a human. On our labelled set of 140 utterances it
  scores 97.9% accuracy with 91% escalation precision, and in the full month it deflects 57% of
  volume — 2,278 requests that never reach an agent."
- **Pain:** **P3** and **P5**.
- **Objection → response:** *"Agents will be fired."* → "Fifty-seven percent of the *simple* volume
  leaves, and the freed hours — 593 a month — go to the work that needs a human. That's the opposite
  of a layoff; it's capacity to grow the order book without hiring 3.5 people."

## 3:45 — Leadership dashboard + SOQL-backed metrics (P4)

- **What you click:** the **Support Console** dashboard tab; then open `docs/soql-reports.md` and run
  the **Backlog by priority** query in the Developer Console.
- **What you say:** "Backlog by priority, first-response cohorts, deflection by topic, SLA breaches
  by agent, warranty claims by product family — all SOQL aggregates, all real-time. This is the weekly
  spreadsheet Marcus rebuilds by hand, but live and correct. Backlog age drops from 34 hours to three."
- **Pain:** **P4**.
- **Objection → response:** *"Can it scale to our numbers?"* → "These are aggregate queries on an
  indexed custom object with one query per batch, not per row. At 4,000 a month you are nowhere near
  the limits; I'll show you the governor-limit math in the appendix."

## 4:30 — Quantified close

- **What you click:** `docs/value-model.md`, then `results/metrics.md`.
- **What you say:** "Same 4,000 requests. First response down 86% — 9.6 hours to 1.3. SLA compliance
  43% to 97%. Deflection 0 to 57%. Backlog 34 hours to three. And the time that releases is 593 agent
  hours a month — **$270,216 a year** at your loaded cost. Your stated target was under two hours'
  first response; we measured 1.3. The next step is a two-week pilot on one topic with Riya's team,
  and we compare the live numbers to this file."
- **Pain:** P1–P5 (close).
- **Objection → response:** *"What's the catch?"* → "The dataset is synthetic and the org isn't
  deployed yet — this is a PoC. The rules are real and portable: deploy with `sf project deploy
  start`, point it at live email-to-case, and the same flow runs on your real traffic."

---

## Technical objection handling (appendix)

| # | Objection | Response |
| --- | --- | --- |
| 1 | **Data model scalability** — "3,000 orders today, what about 300,000?" | Support_Request__c and Order_Record__c are standard indexed custom objects with external-id-friendly email fields; every read is filtered and, where needed, sorted on a single field. Reporting is aggregate SOQL, not row-by-row scans. `SupportMetricsService` issues one query per metric per window. |
| 2 | **Apex governor limits** — "Your trigger will blow up on a bulk load." | The trigger delegates to `SupportRequestTriggerHandler`, which runs **one** SOQL query for the whole batch (lifetime value by email) and does everything else in memory. `tests/test_metadata.py` fails the build if any `.cls` contains a SOQL query inside a for-loop. |
| 3 | **Agent hallucination risk** — "I don't want a bot making up warranty policy." | The agent's Order Status and Warranty answers are produced from `Order_Record__c` rows joined on the customer's email; if no order matches it escalates instead of answering. Only approved `Deflection_Article__c` content is served for policy topics. Confidence below the operating threshold escalates. |
| 4 | **Migration from the shared inbox** — "We have years of email history." | Not in this PoC's scope, and deliberately so: email-to-case can forward new mail on day one while history migration runs in parallel. The metadata in this repo is additive — nothing here changes Sales Cloud objects the sales team uses. |
| 5 | **Licensing / cost** — "What does this add to our bill?" | The data model, Flows, Apex, Lightning app and permission set run on Service Cloud. The deflection assistant is modelled as an Agentforce-style agent; its intent router is also implemented locally so you can validate deflection value *before* committing to a premium AI SKU. |
| 6 | **Security / field-level access** — "Agents shouldn't see pipeline or margins." | `Support_Agent.permissionset-meta.xml` grants create/edit on Support Requests, **read-only** on Orders, and read-only on `Lifetime_Value__c` — agents act on priority without editing commercial data. Object- and field-level access is explicit and version-controlled. |
| 7 | **Quality of the numbers** — "This is synthetic data." | Correct, and stated openly. The PoC's job is to prove the *rules* and the *measurement*; the harness and the Apex implement the same constants so the org will reproduce them. A two-week live pilot is the next step to replace simulated with real. |
