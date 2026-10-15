/**
 * SupportMetricsService
 *
 * The SOQL-backed metrics layer that answers the five questions Dana (VP CX) could not answer during
 * discovery (pain P4). Every method is date-bounded and bulk-safe: aggregate queries and single-pass
 * in-memory math, never a query inside a loop.
 *
 * The same five metrics are computed independently by the local harness (sim/metrics.py) so the
 * org and the reproducible build agree on definitions.
 *
 * @author Solution Engineering
 */
public with sharing class SupportMetricsService {

    /** First-response time summary in minutes. */
    public class FirstResponseResult {
        @AuraEnabled public Decimal meanMinutes;
        @AuraEnabled public Decimal p90Minutes;
        @AuraEnabled public Integer sampleSize;
    }

    /**
     * Requests that received a first response in the window. One query; callers do the math.
     */
    public static List<Support_Request__c> firstResponseSample(Date startDate, Date endDate) {
        return [
            SELECT Id, CreatedDate, First_Response_At__c, SLA_Due__c
            FROM Support_Request__c
            WHERE First_Response_At__c != null
            AND CreatedDate >= :startDate
            AND CreatedDate < :endDate
        ];
    }

    /**
     * M1 - mean and p90 first-response time in minutes for requests created in the window.
     */
    public static FirstResponseResult firstResponseTime(Date startDate, Date endDate) {
        List<Support_Request__c> sample = firstResponseSample(startDate, endDate);
        FirstResponseResult result = new FirstResponseResult();
        result.sampleSize = sample.size();
        if (sample.isEmpty()) {
            result.meanMinutes = 0;
            result.p90Minutes = 0;
            return result;
        }

        List<Decimal> minutes = new List<Decimal>();
        Decimal total = 0;
        for (Support_Request__c req : sample) {
            Long deltaMillis = req.First_Response_At__c.getTime() - req.CreatedDate.getTime();
            Decimal mins = Decimal.valueOf(deltaMillis) / 60000.0;
            minutes.add(mins);
            total += mins;
        }
        minutes.sort();
        result.meanMinutes = (total / sample.size()).setScale(2);
        Integer p90Index = (Integer) Math.min(minutes.size() - 1, Math.floor(minutes.size() * 0.9));
        result.p90Minutes = minutes[p90Index];
        return result;
    }

    /**
     * M2 - percentage of requests resolved without a human touch in the window.
     */
    public static Decimal deflectionRatePct(Date startDate, Date endDate) {
        Integer total = [
            SELECT COUNT()
            FROM Support_Request__c
            WHERE CreatedDate >= :startDate AND CreatedDate < :endDate
        ];
        Integer deflected = [
            SELECT COUNT()
            FROM Support_Request__c
            WHERE Deflected__c = true
            AND CreatedDate >= :startDate AND CreatedDate < :endDate
        ];
        return pct(deflected, total);
    }

    /**
     * M3 - percentage of responded requests whose first response beat SLA_Due__c.
     */
    public static Decimal slaCompliancePct(Date startDate, Date endDate) {
        Integer responded = [
            SELECT COUNT()
            FROM Support_Request__c
            WHERE First_Response_At__c != null
            AND CreatedDate >= :startDate AND CreatedDate < :endDate
        ];
        Integer met = [
            SELECT COUNT()
            FROM Support_Request__c
            WHERE First_Response_At__c != null
            AND First_Response_At__c <= SLA_Due__c
            AND CreatedDate >= :startDate AND CreatedDate < :endDate
        ];
        return pct(met, responded);
    }

    /**
     * M5 - mean age in hours of requests that are not yet Resolved.
     */
    public static Decimal backlogAgeHours(DateTime asOf) {
        DateTime anchor = asOf == null ? DateTime.now() : asOf;
        List<Support_Request__c> open = [
            SELECT Id, CreatedDate
            FROM Support_Request__c
            WHERE Status__c != 'Resolved'
        ];
        if (open.isEmpty()) {
            return 0;
        }
        Decimal totalHours = 0;
        for (Support_Request__c req : open) {
            Long deltaMillis = anchor.getTime() - req.CreatedDate.getTime();
            totalHours += Decimal.valueOf(deltaMillis) / 3600000.0;
        }
        return (totalHours / open.size()).setScale(2);
    }

    /**
     * M4 - requests handled per active agent per working day in the window. The agent count is the
     * number of distinct owners observed, which is the practical headcount of the support pool.
     */
    public static Decimal casesPerAgentPerDay(Date startDate, Date endDate) {
        Integer days = Math.max(1, startDate.daysBetween(endDate));
        List<AggregateResult> byOwner = [
            SELECT OwnerId owner, COUNT(Id) requestCount
            FROM Support_Request__c
            WHERE CreatedDate >= :startDate AND CreatedDate < :endDate
            GROUP BY OwnerId
        ];
        if (byOwner.isEmpty()) {
            return 0;
        }
        Integer total = 0;
        for (AggregateResult row : byOwner) {
            total += (Integer) row.get('requestCount');
        }
        return (Decimal.valueOf(total) / (byOwner.size() * days)).setScale(2);
    }

    /** Percentage helper that never divides by zero. */
    public static Decimal pct(Integer numerator, Integer denominator) {
        if (denominator == null || denominator == 0) {
            return 0;
        }
        return (Decimal.valueOf(numerator == null ? 0 : numerator) * 100.0 / denominator).setScale(2);
    }
}
