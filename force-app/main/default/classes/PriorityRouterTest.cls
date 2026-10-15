/**
 * Unit tests for PriorityRouter.
 *
 * Verifies the scoring is monotonic in lifetime value, the SLA matrix is bounded and ordered, the
 * load balancer spreads work evenly within tolerance, and that a high-value urgent request always
 * outranks a low-value trivial one.
 *
 * @author Solution Engineering
 */
@IsTest
private class PriorityRouterTest {

    @IsTest
    static void scoreIsMonotonicInLifetimeValue() {
        Integer zeroLtv = PriorityRouter.scoreRequest(0, 'Email', 'Store Hours');
        Integer lowLtv = PriorityRouter.scoreRequest(150, 'Email', 'Store Hours');
        Integer midLtv = PriorityRouter.scoreRequest(750, 'Email', 'Store Hours');
        Integer highLtv = PriorityRouter.scoreRequest(1500, 'Email', 'Store Hours');
        Integer topLtv = PriorityRouter.scoreRequest(5000, 'Email', 'Store Hours');

        System.assert(zeroLtv < lowLtv, 'Score must rise from $0 to $150 LTV');
        System.assert(lowLtv < midLtv, 'Score must rise from $150 to $750 LTV');
        System.assert(midLtv < highLtv, 'Score must rise from $750 to $1500 LTV');
        System.assert(highLtv < topLtv, 'Score must rise from $1500 to $5000 LTV');

        // 40 (LTV) + 20 (Phone) + 25 (Warranty) = 85, the maximum possible score.
        System.assertEquals(85, PriorityRouter.scoreRequest(2500, 'Phone', 'Warranty'), 'Max score should be 85');
        System.assertEquals(5, PriorityRouter.scoreRequest(null, 'Email', 'Store Hours'), 'Min score should be 5');
    }

    @IsTest
    static void slaMatrixIsBoundedAndOrdered() {
        System.assertEquals(1440, PriorityRouter.slaMinutesForScore(0), 'Lowest band allows 24h');
        System.assertEquals(480, PriorityRouter.slaMinutesForScore(15), 'Low band begins at 15');
        System.assertEquals(180, PriorityRouter.slaMinutesForScore(30), 'Medium band begins at 30');
        System.assertEquals(60, PriorityRouter.slaMinutesForScore(50), 'High band begins at 50');
        System.assertEquals(15, PriorityRouter.slaMinutesForScore(70), 'Critical band begins at 70');
        System.assertEquals(15, PriorityRouter.slaMinutesForScore(999), 'Scores above the top stay in the top band');

        // The SLA gets stricter (shorter) as the score rises.
        System.assert(
            PriorityRouter.slaMinutesForScore(85) < PriorityRouter.slaMinutesForScore(40),
            'High score must have a tighter SLA than a medium score'
        );

        System.assertEquals('Critical', PriorityRouter.priorityBandForScore(85), 'Max score maps to Critical');
        System.assertEquals('Minimal', PriorityRouter.priorityBandForScore(0), 'Zero score maps to Minimal');

        DateTime start = DateTime.newInstance(2026, 1, 1, 9, 0, 0);
        System.assertEquals(start.addMinutes(15), PriorityRouter.slaDueAt(start, 85), 'SLA due honors the matrix');
    }

    @IsTest
    static void ownerAssignmentIsBalancedWithinTolerance() {
        List<Support_Request__c> requests = new List<Support_Request__c>();
        for (Integer i = 0; i < 9; i++) {
            requests.add(new Support_Request__c(
                Customer_Email__c = 'agent.test' + i + '@northwind.example',
                Status__c = 'New',
                Channel__c = 'Email',
                Topic__c = 'Sizing'
            ));
        }
        insert requests;

        List<Id> agents = new List<Id>{ Id.valueOf('005000000000001'), Id.valueOf('005000000000002'), Id.valueOf('005000000000003') };
        Map<Id, Id> assignment = PriorityRouter.assignOwner(requests, agents);

        System.assertEquals(9, assignment.size(), 'Every request should be assigned');

        Map<Id, Integer> load = new Map<Id, Integer>();
        for (Id agentId : agents) {
            load.put(agentId, 0);
        }
        for (Id agentId : assignment.values()) {
            load.put(agentId, load.get(agentId) + 1);
        }
        Integer minLoad = 9;
        Integer maxLoad = 0;
        for (Integer count : load.values()) {
            minLoad = Math.min(minLoad, count);
            maxLoad = Math.max(maxLoad, count);
        }
        System.assert(maxLoad - minLoad <= 1, 'Load imbalance must be at most one request');
    }

    @IsTest
    static void highValueUrgentBeatsLowValueTrivial() {
        Integer whale = PriorityRouter.scoreRequest(4200, 'Phone', 'Warranty');
        Integer casual = PriorityRouter.scoreRequest(60, 'Email', 'Store Hours');

        System.assert(whale > casual, 'A high-value urgent request must outrank a low-value trivial one');
        System.assert(
            PriorityRouter.slaMinutesForScore(whale) < PriorityRouter.slaMinutesForScore(casual),
            'The higher-value request must get the tighter SLA'
        );
    }
}
