/**
 * Trigger on Support_Request__c.
 *
 * Delegates everything to SupportRequestTriggerHandler so the trigger stays a dispatcher and the
 * logic stays unit-testable and bulk-safe (no SOQL or DML inside the trigger body).
 *
 * @author Solution Engineering
 */
trigger SupportRequestTrigger on Support_Request__c (before insert, before update) {
    if (Trigger.isBefore && Trigger.isInsert) {
        SupportRequestTriggerHandler.onBeforeInsert(Trigger.new);
    } else if (Trigger.isBefore && Trigger.isUpdate) {
        SupportRequestTriggerHandler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
    }
}
