# Org seeding blocker (2026-10-21)

Custom fields created by any API path never reach the org's runtime schema on this
Salesforce release (Winter '27 Patch 8.6, instance USA840).

Evidence (reproduced on Developer Edition orgs `demo`/`demo2` and scratch org `demo3`):

| Path | Result |
|---|---|
| `sf project deploy start` CustomField | Deploy `Succeeded`, `componentSuccesses` lists the field |
| Metadata API retrieve | Field returned (13/13 on Support_Request__c) |
| `sf sobject describe` / SOQL / Apex `getDescribe()` | Field absent (`No such column`) |
| Tooling API `POST /tooling/sobjects/CustomField` | HTTP 201, field never queryable |
| Fresh custom object + one optional field | Object created, field absent |
| API 58, 61, 62, 68 | All fail identically |
| Setup UI field creation (demo2) | Field published immediately (`UI_Probe__c`) |

Objects and required fields (created with the object DDL) *do* publish, so only
post-creation field DDL is broken.

Consequence: seeded priority scoring, warranty checks and deflection cannot run,
because `Priority_Score__c`, `Channel__c`, `Topic__c`, `SLA_Due__c`, `Related_Order__c`,
`Lifetime_Value__c`, `Body__c`, etc. do not exist at runtime.

Working around it requires creating the ~11 fields through Setup UI (the only path that
publishes), or waiting for a Salesforce-side fix.
