/**
 * Invocable wrapper for DeflectionAgentActions.checkOrderStatus.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class CheckOrderStatusAction {
    @InvocableMethod(label='Check Order Status' description='Grounded order-status answer for a customer email.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.checkOrderStatus(requests);
    }
}
