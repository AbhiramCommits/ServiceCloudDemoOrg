# Discovery Brief — Northwind Outfitters

**Prepared by:** Solution Engineering (Service Cloud)
**Customer:** Northwind Outfitters
**Stakeholders interviewed:** VP Customer Experience, Support Team Lead, 3 senior agents, Director of IT, eCommerce Manager
**Engagement:** Proof of Concept — Support Operations Modernization
**Status:** Discovery complete; PoC scoped

---

## 1. Company & Current State

Northwind Outfitters is a B2C outdoor gear retailer headquartered in Bozeman, Montana.

| Attribute | Value |
| --- | --- |
| Employees | 280 |
| Annual revenue | $96M |
| Sales channels | E-commerce (68%), 14 physical stores (32%) |
| Support volume | ~4,000 cases / month (≈48,000 / year) |
| Support agents | 12 (9 general, 2 returns specialists, 1 lead) |
| Current systems | Salesforce Sales Cloud (Accounts, Contacts, Opportunities, Orders sync). **No Service Cloud.** |
| Support tooling today | Shared Gmail inbox (`support@northwindoutfitters.com`), a shared "Case Log.xlsx" tracker on a network drive, a ZenDesk trial that was never fully rolled out |

### Who touches a case today (org chart of the support process)

```
                          ┌──────────────────────────────┐
                          │   VP Customer Experience     │  (economic buyer)
                          │      Dana Whitfield          │
                          └───────────────┬──────────────┘
                                          │
                          ┌───────────────┴──────────────┐
                          │      Support Team Lead       │  (champion)
                          │        Marcus Bell           │
                          └───────────────┬──────────────┘
                                          │
        ┌─────────────────┬──────────────┼──────────────┬──────────────────┐
        │                 │              │              │                  │
  ┌─────┴─────┐    ┌──────┴────┐   ┌─────┴─────┐  ┌─────┴──────┐    ┌──────┴──────┐
  │ 9 General │    │ 2 Returns │   │ 1 Lead    │  │ eCommerce  │    │ Director of │
  │  Agents   │    │ Specialists│  │ (triage)  │  │ Manager    │    │     IT      │
  │           │    │           │   │           │  │  Priya S.  │    │  Tom Reyes  │
  └───────────┘    └───────────┘   └───────────┘  └────────────┘    └─────────────┘
   handle the        handle all      manually       owns the         owns systems,
   shared inbox      RMA/warranty   reads, sorts    store/online     security and
   in shifts         requests       and assigns     split            the "Case Log"
                                                                     spreadsheet
```

### Today's process, step by step

1. Customer emails `support@northwindoutfitters.com` or calls the store line. There is **no web form and no self-service**.
2. Messages land in a **shared Gmail inbox**. The agent on duty reads each message and, if they cannot answer immediately, copies the details into **Case Log.xlsx** — customer email, date, a free-text note, and who is handling it.
3. Priority is decided by **gut feel**. There is no SLA, no priority field, and no relationship between a request and the customer's order history or lifetime value.
4. About **62% of messages** are one of six recurring questions (order status, returns, sizing, shipping, warranty, store hours). Agents answer each one by hand, often re-writing the same reply.
5. Warranty questions are checked by **opening the eCommerce admin console** and eyeballing the order date against Northwind's 12-month gear warranty policy.
6. At the end of the week Marcus exports the spreadsheet by hand and builds a summary for Dana. There is **no real-time view** of backlog, first-response time, or per-agent load.

The result is a support operation that is busy, not measured.

---

## 2. Discovery Questions Asked

### Process

**Q1. Walk me through what happens from the moment a customer hits send to the moment they get an answer.**
> *Dana (VP CX):* "It depends who's on inbox duty. Some emails get answered in twenty minutes, some sit until the next morning. The response is written from scratch every time, and the only record is in the spreadsheet — which is maybe four hours behind reality."

**Q2. How do you decide which requests to work on first, and is that written down anywhere?**
> *Marcus (Team Lead):* "Honestly, whatever looks scary. A return dispute beats a 'where's my order'. We've never written a priority rule down. If a whale customer emails, nothing tells us they're a whale."

**Q3. What happens when an agent is out or is handling something complex?**
> *Marcus:* "The queue just gets deeper. There's no load balancing — whoever is free grabs the next email, and the person who took the last hard one often takes the next hard one too."

### People

**Q4. Who feels the pain most on your team, and what does a bad day look like for them?**
> *Riya (Senior Agent):* "Me, around 4pm. I've answered the same sizing question eleven times and I still haven't touched the two angry return customers. I go home feeling like I did a lot and finished nothing."

**Q5. How do you onboard a new agent into this process today?**
> *Marcus:* "Two weeks of shadowing. They learn the answers by osmosis. There's no knowledge base, so the 'rules' live in our heads."

**Q6. When a customer asks about a warranty, how does the agent make that call?**
> *Riya:* "I open Shopify in another tab, find the order, count the months on my fingers, and guess on the boundary cases. If I get it wrong we eat the return cost."

### Technology

**Q7. What are you using today, and what does the data model look like?**
> *Tom (IT):* "Sales Cloud for the sales team and the customer records. Support is a Gmail inbox and one Excel file. The two worlds don't talk. The order data lives in Shopify; the customer lives in Salesforce. It's the worst of both."

**Q8. If we gave you one screen for support, what must be on it?**
> *Dana:* "The case, the customer's order history, whether they're a good customer, and how long we've got until we've embarrassed ourselves. Right now I'd settle for a case existing at all."

**Q9. What are your hard technical constraints — integrations, security, existing contract commitments?**
> *Tom:* "We're a Salesforce shop on Sales Cloud licensing, so staying on the platform is a win. We need field-level control — agents should see support data, not pipeline. And we can't have a two-year migration."

### Metrics

**Q10. What does 'good' look like for your support team in numbers?**
> *Dana:* "Under a two-hour first response on average. I'd love to deflect a fifth of the simple stuff. And I want our priority customers to never wait."

**Q11. What do you measure today?**
> *Dana:* "Almost nothing. Marcus gives me a weekly count of open tickets. I don't know our first-response time, I don't know our SLA hit rate, I don't know who's drowning."

**Q12. If this PoC works, what number would prove it in a board slide?**
> *Dana:* "Show me first response dropping, deflection going up, and SLA compliance going from 'unknown' to a number I can defend. And show me hours we got back."

**Q13. How much does a repeat question actually cost you?**
> *Marcus:* "If it takes ten to twelve minutes to handle one, and there are thousands of them, that's the whole job. That's where our people go."

---

## 3. Named Pain Points

| ID | Pain Point | Business Impact | Owner |
| --- | --- | --- | --- |
| **P1** | **No single case record / duplicate work across the shared inbox and the spreadsheet.** The same request is typed into two places, and no one can tell who is working what. | ~12 agents × 3.5 hrs/week of re-typing, searching, and "did you take this?" = **~42 hours/week ≈ $83K/year** in duplicated effort. | Marcus Bell (Support Team Lead) |
| **P2** | **No priority or SLA routing — high-value customers wait as long as everyone else.** Priority is gut feel; a first-order buyer and a $4K-LTV repeat gear customer sit in the same FIFO queue. | Slow handling of high-LTV accounts contributes to roughly **8 at-risk customer losses per year** at ~$4,200 average annual value ≈ **$34K/year at risk**, plus repeat-contact cost. | Dana Whitfield (VP CX) |
| **P3** | **Agents answer the same ~6 questions repeatedly** and there is no self-service deflection. | The six recurring topics are **~62% of 4,000 cases/month ≈ 2,480 cases/month**; at ~11 minutes each that is **~455 agent-hours/month ≈ $228K/year** spent on questions a help center could deflect. | Marcus Bell (Support Team Lead) |
| **P4** | **Zero visibility:** leadership cannot see backlog, first-response time, or agent load in real time. | No defensible support KPIs; Marcus spends **~6 hrs/week** hand-building a stale weekly roll-up (≈ **$12K/year**), and misallocation of the 12-agent team is unmeasured. | Dana Whitfield (VP CX) |
| **P5** | **Entitlement/warranty eligibility is checked manually against order history.** Agents tab-hop to the store admin and eyeball order dates against the warranty policy. | ~720 warranty/return requests/month × ~3.5 minutes of manual lookup = **~42 agent-hours/month ≈ $21K/year**, with boundary-case mistakes absorbing return costs. | Riya Anand (Senior Agent) |

*(Labor cost basis: $38/hour fully-loaded agent cost. See `docs/value-model.md` for the full arithmetic and sources.)*

---

## 4. Success Metrics & Today's Stated Baseline

These are the five metrics Dana agreed to judge the PoC against. "Today" values are the customer's stated/estimated baseline from discovery; the local harness in `sim/` re-derives a baseline from synthetic data so each movement is measurable.

| # | Metric | Definition | Today (stated baseline) | PoC Target |
| --- | --- | --- | --- | --- |
| M1 | **First response time** | Mean and p90 minutes from request creation to first agent/assistant response | **~9.4 hours** mean (565 min); no p90 available | Under 2 hours mean |
| M2 | **Deflection rate** | % of incoming requests resolved by self-service / assistant without a human touch | **0%** (no self-service exists) | ≥ 20% |
| M3 | **SLA compliance %** | % of requests whose first response beats their priority-based SLA target | **~41%** (informal, unmeasured) | ≥ 90% |
| M4 | **Cases per agent per day** | Request volume ÷ (agents × working days) | **~16 / agent / day** (4,000 ÷ 12 ÷ 21) | Improve effective capacity without headcount |
| M5 | **Backlog age** | Mean hours a request sits unresolved/open | **~36 hours** (Marcus's rule-of-thumb) | Under 12 hours |

---

## 5. Scope of this Proof of Concept

### In scope

- Stand up a **Support Request data model** on Salesforce (Service Cloud) — the single case record that replaces the inbox + spreadsheet.
- **Automated triage**: priority scoring and SLA assignment from customer lifetime value, channel, and topic.
- An **Agentforce-style deflection assistant** for the six recurring topics, with a human-escalation fallback and grounded answers from order/warranty data.
- **Automated warranty / entitlement eligibility** against order history.
- A **Support Console** Lightning app + record page giving agents one screen and leadership a real-time metrics view.
- A **quantified before/after** produced by running the same business rules over synthetic Northwind-scale data.

### Explicitly out of scope (this PoC)

- Live email-to-case / Gmail or Shopify connectors (deployment requires customer credentials; data movement is simulated locally).
- A full **migration** of historical inbox + spreadsheet data.
- LLM fine-tuning or a production Agentforce Einstein trust-layer configuration on the customer's org.
- Telephony / CTI, chat widget, and multi-language support.
- Marketing Cloud, Data Cloud ingestion, and any sales-side process changes.
- Formal SLA contracting and legal entitlement terms.

---

## 6. Stakeholder Map

| Role | Name | What they need to hear |
| --- | --- | --- |
| **Economic buyer** | Dana Whitfield, VP Customer Experience | That the PoC moves first-response time, deflection, and SLA compliance **with hard numbers**, and that the same team can absorb the new process. She signs the budget and defends the number to the board. |
| **Champion** | Marcus Bell, Support Team Lead | That agents get a single screen, that priority rules are consistent and explainable, and that he can finally see backlog and per-agent load without hand-building a spreadsheet. He drives adoption. |
| **Technical evaluator** | Tom Reyes, Director of IT | That it is **native Salesforce DX metadata** he can deploy and review, that security is field-level and permissioned, that Apex is bulk-safe and governor-limit aware, and that there is no two-year migration. He signs the technical "no". |
| **Blocker** | Riya Anand, Senior Agent (and by extension the agent team) | That the deflection assistant **escalates instead of guessing**, that it does not surveil them, and that it removes the copy-paste and manual warranty lookup rather than adding a new tool to learn. If she objects, adoption dies. |
