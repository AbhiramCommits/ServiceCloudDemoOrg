/**
 * SupportRequestTriggerHandler
 *
 * All support-request trigger logic lives here so the trigger body stays a one-line dispatcher.
 * Bulk-safe by construction: the before-insert path issues exactly one SOQL query for the whole
 * batch (customer lifetime value by email) and every loop operates purely on in-memory data.
 *
 * Addresses P1 (single record + related order context), P2 (score + SLA) and P4 (status lifecycle).
 *
 * @author Solution Engineering
 */
public with sharing class SupportRequestTriggerHandler {

    /**
     * Before-insert: score the request, stamp its priority band and SLA due date, relate it to the
     * customer's order, and move it to Triaged.
     */
    public static void onBeforeInsert(List<Support_Request__c> newRequests) {
        Map<String, Decimal> ltvByEmail = new Map<String, Decimal>();
        Map<String, Id> orderIdByEmail = new Map<String, Id>();

        Set<String> emails = new Set<String>();
        for (Support_Request__c req : newRequests) {
            if (String.isNotBlank(req.Customer_Email__c)) {
                emails.add(req.Customer_Email__c);
            }
        }

        if (!emails.isEmpty()) {
            List<Order_Record__c> orders = [
                SELECT Id, Customer_Email__c, Lifetime_Value__c
                FROM Order_Record__c
                WHERE Customer_Email__c IN :emails
                ORDER BY Lifetime_Value__c DESC NULLS LAST
            ];
            for (Order_Record__c order : orders) {
                if (order.Customer_Email__c == null) {
                    continue;
                }
                String key = order.Customer_Email__c.toLowerCase();
                if (!ltvByEmail.containsKey(key)) {
                    ltvByEmail.put(key, order.Lifetime_Value__c);
                    orderIdByEmail.put(key, order.Id);
                }
            }
        }

        for (Support_Request__c req : newRequests) {
            applyTriage(req, ltvByEmail, orderIdByEmail);
        }
    }

    /**
     * Before-update: re-stamp the SLA if a triage input changed, and stamp the first-response
     * timestamp the moment an agent engages the request.
     */
    public static void onBeforeUpdate(List<Support_Request__c> newRequests, Map<Id, Support_Request__c> oldMap) {
        for (Support_Request__c req : newRequests) {
            Support_Request__c old = oldMap == null ? null : oldMap.get(req.Id);
            Boolean triageInputsChanged = old == null
                || old.Topic__c != req.Topic__c
                || old.Channel__c != req.Channel__c
                || old.Priority_Score__c != req.Priority_Score__c;

            if (triageInputsChanged && req.Priority_Score__c != null) {
                req.SLA_Due__c = PriorityRouter.slaDueAt(req.CreatedDate, (Integer) req.Priority_Score__c);
            }

            if (req.First_Response_At__c == null
                && (req.Status__c == 'In Progress' || req.Status__c == 'Resolved')) {
                req.First_Response_At__c = DateTime.now();
            }
        }
    }

    /** Shared scoring/triage application used by the insert path. */
    private static void applyTriage(
        Support_Request__c req,
        Map<String, Decimal> ltvByEmail,
        Map<String, Id> orderIdByEmail
    ) {
        String key = req.Customer_Email__c == null ? null : req.Customer_Email__c.toLowerCase();
        Decimal ltv = key == null ? null : ltvByEmail.get(key);

        Integer score = PriorityRouter.scoreRequest(ltv, req.Channel__c, req.Topic__c);
        req.Priority_Score__c = score;
        req.Priority__c = PriorityRouter.priorityBandForScore(score);

        DateTime created = req.CreatedDate == null ? DateTime.now() : req.CreatedDate;
        req.SLA_Due__c = PriorityRouter.slaDueAt(created, score);

        if (String.isBlank(req.Status__c) || req.Status__c == 'New') {
            req.Status__c = 'Triaged';
        }
        if (req.Related_Order__c == null && key != null && orderIdByEmail.containsKey(key)) {
            req.Related_Order__c = orderIdByEmail.get(key);
        }
    }
}
