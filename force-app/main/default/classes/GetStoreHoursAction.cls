/**
 * Invocable wrapper for DeflectionAgentActions.getStoreHours.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class GetStoreHoursAction {
    @InvocableMethod(label='Get Store Hours' description='Return store hours and locator guidance.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.getStoreHours(requests);
    }
}
