/**
 * Invocable wrapper for DeflectionAgentActions.startReturn.
 *
 * Apex permits a single @InvocableMethod per class, so each agent action gets its own thin
 * entry point that delegates to the shared, bulk-safe implementation.
 */
public with sharing class StartReturnAction {
    @InvocableMethod(label='Start Return' description='Open a return for the customer\'s most recent order.')
    public static List<DeflectionAgentActions.AgentResponse> run(
        List<DeflectionAgentActions.AgentRequest> requests
    ) {
        return DeflectionAgentActions.startReturn(requests);
    }
}
