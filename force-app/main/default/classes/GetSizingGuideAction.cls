/**
 * Invocable wrapper for DeflectionAgentActions.getSizingGuide.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class GetSizingGuideAction {
    @InvocableMethod(label='Get Sizing Guide' description='Return approved sizing guidance.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.getSizingGuide(requests);
    }
}
