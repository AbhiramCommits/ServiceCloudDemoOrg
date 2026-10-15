# Requirements Traceability — Northwind Outfitters

Every named pain from `docs/discovery-brief.md` mapped to a business requirement, the Salesforce
capability that satisfies it, the concrete artifact(s) in this repo, and the metric movement
(produced by `sim/`, sourced from `results/metrics.json`).

> Paths under `force-app/` are deployable SFDX metadata. Paths under `sim/` are the local harness
> that mirrors the same business rules so results are reproducible without an org. The **Metric
> Moved** column is filled from real simulation output in `results/metrics.json`.

| Pain ID | Business Requirement | Salesforce Capability | Where It Lives in This Repo | Metric Moved |
| --- | --- | --- | --- | --- |
| P1 | One durable record per customer request, joined to the customer's order and visible to the whole team instead of the shared inbox plus spreadsheet. | Service Cloud custom object `Support_Request__c` with a related-order lookup, a record-triggered lifecycle, and a Lightning record page. | `force-app/main/default/objects/Support_Request__c/`, `force-app/main/default/flexipages/Support_Console_Record_Page.flexipage-meta.xml`, `force-app/main/default/triggers/SupportRequestTrigger.trigger`, `sim/run_simulation.py` | TODO |
| P2 | Score every request by customer lifetime value, channel and topic; assign a priority-based SLA; and route work so high-value requests never queue behind low-value ones. | Record-triggered Flow triage plus `PriorityRouter` Apex scoring, the SLA matrix, least-loaded owner assignment, and a scheduled escalation path. | `force-app/main/default/flows/Support_Request_Triage.flow-meta.xml`, `force-app/main/default/classes/PriorityRouter.cls`, `force-app/main/default/flows/Case_Escalation_Alert.flow-meta.xml`, `sim/priority_router.py` | TODO |
| P3 | Deflect the six recurring questions through self-service and escalate anything the assistant cannot ground. | Agentforce-style deflection agent with six invocable Apex actions, deflection articles, and an intent router with a confidence threshold. | `force-app/main/default/classes/DeflectionAgentActions.cls`, `agentforce/deflection-agent.md`, `force-app/main/default/objects/Deflection_Article__c/`, `sim/assistant.py`, `data/intent_eval.csv` | TODO |
| P4 | Give leadership real-time visibility into backlog, first-response time, SLA compliance and agent load. | SOQL aggregate metrics service, the Support Console Lightning app with a dashboard tab, and named reporting queries. | `force-app/main/default/classes/SupportMetricsService.cls`, `force-app/main/default/applications/Support_Console.app-meta.xml`, `docs/soql-reports.md`, `sim/metrics.py` | TODO |
| P5 | Determine warranty / entitlement eligibility automatically from the customer's order history. | `WarrantyService` Apex plus the `Warranty_Eligibility_Check` Flow over the order data model. | `force-app/main/default/classes/WarrantyService.cls`, `force-app/main/default/flows/Warranty_Eligibility_Check.flow-meta.xml`, `force-app/main/default/objects/Order_Record__c/`, `sim/warranty.py` | TODO |
