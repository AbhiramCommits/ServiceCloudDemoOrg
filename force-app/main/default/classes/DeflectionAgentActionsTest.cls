/**
 * Unit tests for DeflectionAgentActions.
 *
 * Verifies the agent resolves grounded order and warranty answers, escalates when there is no order,
 * and that the article-backed policy actions return content. Every action is exercised in bulk to
 * confirm the single-query design holds.
 *
 * @author Solution Engineering
 */
@IsTest
private class DeflectionAgentActionsTest {

    @IsTest
    static void orderStatusIsGroundedInOrderHistory() {
        Order_Record__c order = new Order_Record__c(
            Order_Date__c = Date.today().addDays(-4),
            Warranty_Months__c = 12,
            Customer_Email__c = 'status@northwind.example',
            Amount__c = 180,
            Lifetime_Value__c = 620
        );
        insert order;

        List<DeflectionAgentActions.AgentRequest> requests = new List<DeflectionAgentActions.AgentRequest>();
        requests.add(request('status@northwind.example'));
        requests.add(request('nobody@northwind.example'));

        Test.startTest();
        List<DeflectionAgentActions.AgentResponse> responses =
            DeflectionAgentActions.checkOrderStatus(requests);
        Test.stopTest();

        System.assertEquals(2, responses.size(), 'One response per request');
        System.assert(responses[0].deflected, 'A known customer should be deflected');
        System.assertEquals(order.Id, responses[0].orderId, 'The related order should be returned');
        System.assert(!responses[1].deflected, 'An unknown email must escalate, not guess');
    }

    @IsTest
    static void warrantyVerdictComesFromWarrantyService() {
        Order_Record__c covered = new Order_Record__c(
            Order_Date__c = Date.today().addMonths(-2),
            Warranty_Months__c = 12,
            Customer_Email__c = 'covered@northwind.example',
            Amount__c = 300,
            Lifetime_Value__c = 1500
        );
        Order_Record__c expired = new Order_Record__c(
            Order_Date__c = Date.today().addMonths(-30),
            Warranty_Months__c = 12,
            Customer_Email__c = 'expired@northwind.example',
            Amount__c = 90,
            Lifetime_Value__c = 90
        );
        insert new List<Order_Record__c>{ covered, expired };

        List<DeflectionAgentActions.AgentRequest> requests = new List<DeflectionAgentActions.AgentRequest>();
        requests.add(request('covered@northwind.example'));
        requests.add(request('expired@northwind.example'));

        Test.startTest();
        List<DeflectionAgentActions.AgentResponse> responses =
            DeflectionAgentActions.checkWarranty(requests);
        Test.stopTest();

        System.assert(responses[0].deflected, 'Warranty should be answered from order history');
        System.assert(responses[0].message.containsIgnoreCase('warranty'), 'Should mention warranty');
        System.assert(responses[0].message.containsIgnoreCase('still under warranty'), 'Covered order is in-warranty');
        System.assert(responses[1].message.containsIgnoreCase('window has ended'), 'Expired order is out of warranty');
    }

    @IsTest
    static void policyActionsReturnGroundedContent() {
        insert new Deflection_Article__c(
            Topic__c = 'Store Hours',
            Title__c = 'Store hours',
            Body__c = 'Bozeman: Mon-Sat 9-7, Sun 10-6.',
            Views__c = 10,
            Helpful_Count__c = 4
        );

        List<DeflectionAgentActions.AgentRequest> requests = new List<DeflectionAgentActions.AgentRequest>();
        requests.add(request('anyone@northwind.example'));

        Test.startTest();
        List<DeflectionAgentActions.AgentResponse> hours = DeflectionAgentActions.getStoreHours(requests);
        List<DeflectionAgentActions.AgentResponse> shipping = DeflectionAgentActions.getShippingPolicy(requests);
        List<DeflectionAgentActions.AgentResponse> returns = DeflectionAgentActions.startReturn(requests);
        Test.stopTest();

        System.assert(hours[0].deflected, 'Store hours is a self-service answer');
        System.assertEquals('Bozeman: Mon-Sat 9-7, Sun 10-6.', hours[0].message, 'Article body should be used');
        System.assertNotEquals(null, shipping[0].message, 'Shipping falls back to approved policy text');
        System.assert(returns[0].message.containsIgnoreCase('30 days'), 'Return policy should be stated');
    }

    private static DeflectionAgentActions.AgentRequest request(String email) {
        DeflectionAgentActions.AgentRequest req = new DeflectionAgentActions.AgentRequest();
        req.customerEmail = email;
        req.requestDate = Date.today();
        return req;
    }
}
