/**
 * Unit tests for the six @InvocableMethod wrapper classes.
 *
 * Apex allows one invocable method per class, so each agent action has its own entry point. This
 * test invokes every wrapper to confirm the delegation and the bulk response shape.
 */
@IsTest
private class DeflectionAgentActionWrappersTest {

    @IsTest
    static void allWrappersReturnOneResponsePerRequest() {
        insert new Order_Record__c(
            Customer_Email__c = 'wrapper@northwind.example',
            Order_Date__c = Date.today().addDays(-10),
            Warranty_Months__c = 12,
            Amount__c = 120,
            Lifetime_Value__c = 600
        );
        insert new Deflection_Article__c(
            Topic__c = 'Shipping',
            Title__c = 'Shipping options',
            Body__c = 'Free standard shipping over $75.',
            Views__c = 5,
            Helpful_Count__c = 2
        );

        DeflectionAgentActions.AgentRequest request = new DeflectionAgentActions.AgentRequest();
        request.customerEmail = 'wrapper@northwind.example';
        request.requestDate = Date.today();
        List<DeflectionAgentActions.AgentRequest> requests =
            new List<DeflectionAgentActions.AgentRequest>{ request };

        Test.startTest();
        List<DeflectionAgentActions.AgentResponse> status = CheckOrderStatusAction.run(requests);
        List<DeflectionAgentActions.AgentResponse> returns = StartReturnAction.run(requests);
        List<DeflectionAgentActions.AgentResponse> sizing = GetSizingGuideAction.run(requests);
        List<DeflectionAgentActions.AgentResponse> shipping = GetShippingPolicyAction.run(requests);
        List<DeflectionAgentActions.AgentResponse> hours = GetStoreHoursAction.run(requests);
        List<DeflectionAgentActions.AgentResponse> warranty = CheckWarrantyAction.run(requests);
        Test.stopTest();

        System.assertEquals(1, status.size());
        System.assertEquals(1, returns.size());
        System.assertEquals(1, sizing.size());
        System.assertEquals(1, shipping.size());
        System.assertEquals(1, hours.size());
        System.assertEquals(1, warranty.size());

        System.assert(status[0].deflected, 'Known customer order is answered');
        System.assertNotEquals(null, status[0].orderId, 'Order id is returned');
        System.assertEquals('CheckWarranty', warranty[0].action);
        System.assertEquals('Free standard shipping over $75.', shipping[0].message,
            'Article body backs the shipping answer');
        System.assert(returns[0].message.containsIgnoreCase('30 days'));
    }
}
