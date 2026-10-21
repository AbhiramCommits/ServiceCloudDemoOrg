/**
 * Invocable wrapper for DeflectionAgentActions.getShippingPolicy.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class GetShippingPolicyAction {
    @InvocableMethod(label='Get Shipping Policy' description='Return approved shipping options and timeframes.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.getShippingPolicy(requests);
    }
}
