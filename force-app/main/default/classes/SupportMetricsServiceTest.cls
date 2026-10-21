/**
 * Unit tests for SupportMetricsService.
 *
 * Exercises each metric against real inserted rows so the SOQL paths and the in-memory math are
 * both covered, plus the empty-window and divide-by-zero guards.
 */
@IsTest
private class SupportMetricsServiceTest {

    @IsTest
    static void metricsAreComputedFromRequests() {
        Date startDate = Date.today().addDays(-5);
        Date endDate = Date.today().addDays(5);

        List<Support_Request__c> requests = new List<Support_Request__c>{
            new Support_Request__c(
                Customer_Email__c = 'metrics.one@northwind.example',
                Channel__c = 'Email',
                Topic__c = 'Warranty'
            ),
            new Support_Request__c(
                Customer_Email__c = 'metrics.two@northwind.example',
                Channel__c = 'Chat',
                Topic__c = 'Shipping'
            )
        };
        insert requests;

        Support_Request__c responded = [
            SELECT Id, SLA_Due__c
            FROM Support_Request__c
            WHERE Id = :requests[0].Id
        ];
        System.assertNotEquals(null, responded.SLA_Due__c, 'Triage should stamp an SLA due date');

        update new Support_Request__c(
            Id = responded.Id,
            First_Response_At__c = DateTime.now(),
            Deflected__c = true
        );

        Test.startTest();
        SupportMetricsService.FirstResponseResult firstResponse =
            SupportMetricsService.firstResponseTime(startDate, endDate);
        Decimal deflection = SupportMetricsService.deflectionRatePct(startDate, endDate);
        Decimal sla = SupportMetricsService.slaCompliancePct(startDate, endDate);
        Decimal backlog = SupportMetricsService.backlogAgeHours(DateTime.now());
        Decimal perAgent = SupportMetricsService.casesPerAgentPerDay(startDate, endDate);
        Decimal guarded = SupportMetricsService.pct(0, 0);
        Test.stopTest();

        System.assertEquals(1, firstResponse.sampleSize, 'Only the responded request is in the sample');
        System.assert(firstResponse.meanMinutes >= 0, 'Mean first-response time is non-negative');
        System.assert(firstResponse.p90Minutes >= 0, 'p90 first-response time is non-negative');
        System.assert(deflection > 0 && deflection <= 100, 'Deflection rate is a percentage');
        System.assert(sla >= 0 && sla <= 100, 'SLA compliance is a percentage');
        System.assert(backlog >= 0, 'Backlog age is non-negative');
        System.assert(perAgent > 0, 'Cases per agent per day is positive');
        System.assertEquals(0.0, guarded, 'Divide-by-zero returns zero');
    }

    @IsTest
    static void emptyWindowReturnsZeros() {
        Date startDate = Date.today().addDays(-30);
        Date endDate = startDate.addDays(1);

        Test.startTest();
        System.assertEquals(0, SupportMetricsService.firstResponseTime(startDate, endDate).sampleSize);
        System.assertEquals(0.0, SupportMetricsService.deflectionRatePct(startDate, endDate));
        System.assertEquals(0.0, SupportMetricsService.slaCompliancePct(startDate, endDate));
        System.assertEquals(0.0, SupportMetricsService.backlogAgeHours(DateTime.now()));
        System.assertEquals(0.0, SupportMetricsService.casesPerAgentPerDay(startDate, endDate));
        Test.stopTest();
    }
}
