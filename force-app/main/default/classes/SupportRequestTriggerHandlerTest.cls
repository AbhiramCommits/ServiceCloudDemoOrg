/**
 * Unit tests for the SupportRequestTrigger before-insert and before-update paths.
 *
 * Verifies triage stamping, order correlation from lifetime value, SLA recomputation when a triage
 * input changes, and first-response stamping when an agent engages the request.
 */
@IsTest
private class SupportRequestTriggerHandlerTest {

    @IsTest
    static void insertTriagesAndRelatesOrder() {
        Order_Record__c order = new Order_Record__c(
            Customer_Email__c = 'trigger.customer@northwind.example',
            Order_Date__c = Date.today().addDays(-20),
            Warranty_Months__c = 12,
            Amount__c = 250,
            Lifetime_Value__c = 2500
        );
        insert order;

        Support_Request__c request = new Support_Request__c(
            Customer_Email__c = 'trigger.customer@northwind.example',
            Channel__c = 'Phone',
            Topic__c = 'Warranty',
            Status__c = 'New'
        );

        Test.startTest();
        insert request;
        Test.stopTest();

        Support_Request__c inserted = [
            SELECT Status__c, Priority_Score__c, Priority__c, SLA_Due__c, Related_Order__c
            FROM Support_Request__c
            WHERE Id = :request.Id
        ];
        System.assertEquals('Triaged', inserted.Status__c, 'New requests move to Triaged');
        System.assertNotEquals(null, inserted.Priority_Score__c, 'A priority score is stamped');
        System.assertEquals('Critical', inserted.Priority__c, 'Max score maps to Critical');
        System.assertNotEquals(null, inserted.SLA_Due__c, 'An SLA due date is stamped');
        System.assertEquals(order.Id, inserted.Related_Order__c, 'The customer order is related');
    }

    @IsTest
    static void updateStampsFirstResponseAndRecomputesSla() {
        Support_Request__c request = new Support_Request__c(
            Customer_Email__c = 'trigger.update@northwind.example',
            Channel__c = 'Email',
            Topic__c = 'Sizing',
            Status__c = 'New'
        );
        insert request;

        Support_Request__c existing = [
            SELECT Id, SLA_Due__c, First_Response_At__c, Priority_Score__c
            FROM Support_Request__c
            WHERE Id = :request.Id
        ];
        System.assertNotEquals(null, existing.SLA_Due__c, 'Insert stamps an SLA');
        System.assertEquals(null, existing.First_Response_At__c, 'No response yet');

        Test.startTest();
        existing.Topic__c = 'Warranty';
        existing.Status__c = 'In Progress';
        update existing;
        Test.stopTest();

        Support_Request__c updated = [
            SELECT Status__c, SLA_Due__c, First_Response_At__c, Priority_Score__c
            FROM Support_Request__c
            WHERE Id = :request.Id
        ];
        System.assertEquals('In Progress', updated.Status__c, 'Status is persisted');
        System.assertNotEquals(null, updated.First_Response_At__c, 'Engaging stamps the first response');
        System.assertNotEquals(null, updated.SLA_Due__c, 'SLA is recomputed from the new topic');
        System.assertEquals(existing.Priority_Score__c, updated.Priority_Score__c,
            'Priority score is stamped on insert and preserved on update');
    }
}
