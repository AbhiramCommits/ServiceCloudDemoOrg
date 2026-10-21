/**
 * Invocable wrapper for DeflectionAgentActions.checkWarranty.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class CheckWarrantyAction {
    @InvocableMethod(label='Check Warranty' description='Grounded warranty verdict from order history.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.checkWarranty(requests);
    }
}
