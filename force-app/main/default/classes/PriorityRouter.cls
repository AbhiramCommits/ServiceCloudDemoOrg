/**
 * PriorityRouter
 *
 * Single source of truth for Northwind Outfitters' support triage:
 *   - a composite priority score built from customer lifetime value, channel and topic (pain P2)
 *   - the priority-band -> SLA matrix that stamps SLA_Due__c
 *   - deterministic, load-balanced owner assignment across the agent pool
 *
 * The scoring constants and SLA matrix are mirrored exactly by the local harness
 * (sim/config.py + sim/priority_router.py) so the before/after numbers in results/ are reproducible
 * without a live org. If you change a constant here, change it there too.
 *
 * No SOQL and no DML live in this class; it is a pure calculation utility so it is cheap to unit test.
 *
 * @author  Solution Engineering
 */
public with sharing class PriorityRouter {

    /** Lifetime-value tiers (USD), evaluated highest-first. Points are positionally aligned. */
    public static final List<Decimal> LTV_THRESHOLDS = new List<Decimal>{ 2000, 1000, 500, 100 };
    public static final List<Integer> LTV_POINTS = new List<Integer>{ 40, 30, 20, 10 };

    /** Intake-channel urgency, higher = more urgent. */
    public static final Map<String, Integer> CHANNEL_POINTS = new Map<String, Integer>{
        'Phone' => 20,
        'Chat' => 15,
        'Web' => 10,
        'Email' => 5
    };

    /** Topic urgency. Warranty and Return are the highest-stakes recurring questions. */
    public static final Map<String, Integer> TOPIC_POINTS = new Map<String, Integer>{
        'Warranty' => 25,
        'Return' => 20,
        'Order Status' => 15,
        'Shipping' => 10,
        'Other' => 8,
        'Sizing' => 5,
        'Store Hours' => 0
    };

    /** SLA matrix: score threshold -> minutes allowed for a first response, highest-first. */
    public static final List<Integer> SLA_SCORE_THRESHOLDS = new List<Integer>{ 70, 50, 30, 15, 0 };
    public static final List<Integer> SLA_MINUTES = new List<Integer>{ 30, 120, 480, 1440, 2880 };
    public static final List<String> SLA_BANDS = new List<String>{ 'Critical', 'High', 'Medium', 'Low', 'Minimal' };

    /**
     * Composite priority score, 0..85.
     *
     * @param lifetimeValue customer lifetime value in USD (null treated as 0)
     * @param channel       intake channel (Email/Web/Chat/Phone)
     * @param topic         the recurring-question topic (or Other)
     * @return integer score, higher means more urgent
     */
    public static Integer scoreRequest(Decimal lifetimeValue, String channel, String topic) {
        return ltvPoints(lifetimeValue) + channelPoints(channel) + topicPoints(topic);
    }

    /** Points contributed by lifetime value. Monotonically non-decreasing in lifetimeValue. */
    public static Integer ltvPoints(Decimal lifetimeValue) {
        Decimal ltv = lifetimeValue == null ? 0 : lifetimeValue;
        for (Integer i = 0; i < LTV_THRESHOLDS.size(); i++) {
            if (ltv >= LTV_THRESHOLDS[i]) {
                return LTV_POINTS[i];
            }
        }
        return 0;
    }

    /** Points contributed by intake channel. Unknown channels score 0. */
    public static Integer channelPoints(String channel) {
        if (channel == null || !CHANNEL_POINTS.containsKey(channel)) {
            return 0;
        }
        return CHANNEL_POINTS.get(channel);
    }

    /** Points contributed by topic. Unknown topics score 0. */
    public static Integer topicPoints(String topic) {
        if (topic == null || !TOPIC_POINTS.containsKey(topic)) {
            return 0;
        }
        return TOPIC_POINTS.get(topic);
    }

    /** Minutes of first-response SLA allowed for a given score. */
    public static Integer slaMinutesForScore(Integer score) {
        Integer s = score == null ? 0 : score;
        for (Integer i = 0; i < SLA_SCORE_THRESHOLDS.size(); i++) {
            if (s >= SLA_SCORE_THRESHOLDS[i]) {
                return SLA_MINUTES[i];
            }
        }
        return SLA_MINUTES[SLA_MINUTES.size() - 1];
    }

    /** Priority band label for a given score (Critical/High/Medium/Low/Minimal). */
    public static String priorityBandForScore(Integer score) {
        Integer s = score == null ? 0 : score;
        for (Integer i = 0; i < SLA_SCORE_THRESHOLDS.size(); i++) {
            if (s >= SLA_SCORE_THRESHOLDS[i]) {
                return SLA_BANDS[i];
            }
        }
        return SLA_BANDS[SLA_BANDS.size() - 1];
    }

    /** Timestamp the SLA is due, given when the request arrived and its score. */
    public static DateTime slaDueAt(DateTime start, Integer score) {
        DateTime base = start == null ? DateTime.now() : start;
        return base.addMinutes(slaMinutesForScore(score));
    }

    /**
     * Load-balance a batch of requests across the agent pool.
     *
     * Greedy least-loaded assignment with a deterministic tie-break on the agent's Id, so the same
     * input always produces the same assignment (and matches sim/priority_router.py). OwnerId is set
     * in memory; the caller performs DML. Bulk-safe: no SOQL, no DML, no per-row queries.
     *
     * @param requests the requests to assign (must have Id set when used after insert)
     * @param agentIds the pool of agent User Ids
     * @return map of request Id -> chosen agent Id
     */
    public static Map<Id, Id> assignOwner(List<Support_Request__c> requests, List<Id> agentIds) {
        Map<Id, Id> assignment = new Map<Id, Id>();
        if (requests == null || requests.isEmpty() || agentIds == null || agentIds.isEmpty()) {
            return assignment;
        }

        List<Id> pool = new List<Id>(agentIds);
        pool.sort();

        Map<Id, Integer> load = new Map<Id, Integer>();
        for (Id agentId : pool) {
            load.put(agentId, 0);
        }

        for (Support_Request__c req : requests) {
            Id chosen = pool[0];
            Integer lowest = load.get(chosen);
            for (Id agentId : pool) {
                if (load.get(agentId) < lowest) {
                    chosen = agentId;
                    lowest = load.get(agentId);
                }
            }
            assignment.put(req.Id, chosen);
            load.put(chosen, lowest + 1);
        }
        return assignment;
    }

    /** Convenience overload that stamps OwnerId directly on the in-memory records. */
    public static void assignOwnerInPlace(List<Support_Request__c> requests, List<Id> agentIds) {
        Map<Id, Id> assignment = assignOwner(requests, agentIds);
        for (Support_Request__c req : requests) {
            if (req.Id != null && assignment.containsKey(req.Id)) {
                req.OwnerId = assignment.get(req.Id);
            }
        }
    }
}
