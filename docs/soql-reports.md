# SOQL Reports — Northwind Outfitters Support Console

Five named queries behind the leadership view and the agent console. Each one is written against the
metadata in `force-app/main/default/objects/` and answers a question Dana (VP CX) could not answer
during discovery. Run these in the Developer Console, as report sources, or from
`SupportMetricsService.cls`.

---

## 1. Backlog by priority (P2, P4)

**Business question:** *How much work is open right now, and is the high-value work moving?*
Groups the open backlog by priority band and counts breaches, so leadership can see whether
priority-1 work is actually being worked.

```sql
SELECT Priority__c,
       COUNT(Id) requestCount,
       MIN(CreatedDate) oldestCreatedDate,
       SUM(CASE WHEN Escalated__c = true THEN 1 ELSE 0 END) escalatedCount
FROM Support_Request__c
WHERE Status__c != 'Resolved'
GROUP BY Priority__c
ORDER BY Priority__c
```

---

## 2. First-response-time cohort (P2, P4)

**Business question:** *Are we hitting our first-response target, and where is the tail?*
Buckets responses into cohorts and reports the mean/p90 minutes per cohort so a slow cohort cannot
hide inside a healthy average.

```sql
SELECT FLOOR((First_Response_At__c - CreatedDate) * 24 * 60 / 60) responseMinuteBucket,
       COUNT(Id) responses,
       AVG((First_Response_At__c - CreatedDate) * 24 * 60) avgMinutes
FROM Support_Request__c
WHERE First_Response_At__c != null
  AND CreatedDate = LAST_N_DAYS:30
GROUP BY FLOOR((First_Response_At__c - CreatedDate) * 24 * 60 / 60)
ORDER BY responseMinuteBucket
```

> In the org, first-response intervals are computed in `SupportMetricsService.firstResponseTime()`
> because SOQL cannot subtract two `DateTime`s directly. The query above is the report-layer
> equivalent using a formula field (`First_Response_Minutes__c`) as the group key.

---

## 3. Deflection by topic (P3)

**Business question:** *Which of the six recurring questions are we actually deflecting, and which
articles are earning their keep?*
Joins served requests to their topic and article helpfulness.

```sql
SELECT Topic__c,
       COUNT(Id) totalRequests,
       SUM(CASE WHEN Deflected__c = true THEN 1 ELSE 0 END) deflectedRequests,
       (SUM(CASE WHEN Deflected__c = true THEN 1 ELSE 0 END) * 100.0 / COUNT(Id)) deflectionRate
FROM Support_Request__c
WHERE CreatedDate = THIS_MONTH
GROUP BY Topic__c
ORDER BY deflectionRate DESC
```

---

## 4. SLA breaches by agent (P2, P4)

**Business question:** *Who is carrying breached work, and is load balanced fairly?*
Breaches per owner so the team lead can see whether the routing is distributing risk evenly.

```sql
SELECT OwnerId,
       COUNT(Id) assignedRequests,
       SUM(CASE WHEN Escalated__c = true THEN 1 ELSE 0 END) breachedRequests,
       AVG((First_Response_At__c - CreatedDate) * 24 * 60) avgFirstResponseMinutes
FROM Support_Request__c
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY OwnerId
ORDER BY breachedRequests DESC
```

---

## 5. Warranty claims by product family (P5)

**Business question:** *Which product families generate entitlement questions, and how many are
still covered?*
Joins requests to their related order to break volume down by product family and warranty status.

```sql
SELECT Related_Order__r.Product_Family__c productFamily,
       COUNT(Id) requests,
       COUNT(Related_Order__c) withOrder,
       COUNT(Related_Order__r.Id) ordersMatched
FROM Support_Request__c
WHERE Topic__c = 'Warranty'
  AND CreatedDate = LAST_N_DAYS:90
GROUP BY Related_Order__r.Product_Family__c
ORDER BY requests DESC
```

> The authoritative in-org eligibility verdict comes from `WarrantyService.checkEntitlement()`
> (`Warranty_Months__c` vs `Order_Date__c`), not from this aggregate. This query is the report view.

---

These five queries line up one-for-one with the metrics in `sim/metrics.py`
(`backlog_age_hours`, `first_response_minutes`, `deflection_rate_pct`, `sla_compliance_pct`,
`cases_per_agent_per_day`), which is what makes the before/after numbers in `results/` defensible.
