/**
 * Unit tests for WarrantyService.
 *
 * Covers inside / outside / exact-boundary warranty dates, missing orders, zero-month coverage, and
 * the bulk entitlement path against a real inserted order.
 *
 * @author Solution Engineering
 */
@IsTest
private class WarrantyServiceTest {

    @IsTest
    static void insideWarrantyWindowIsCovered() {
        Date orderDate = Date.newInstance(2025, 1, 15);
        System.assert(
            WarrantyService.isUnderWarranty(orderDate, 12, Date.newInstance(2025, 6, 1)),
            'Six months into a twelve-month warranty must be covered'
        );
    }

    @IsTest
    static void outsideWarrantyWindowIsNotCovered() {
        Date orderDate = Date.newInstance(2024, 1, 15);
        System.assert(
            !WarrantyService.isUnderWarranty(orderDate, 12, Date.newInstance(2025, 3, 1)),
            'Later than the expiry must not be covered'
        );
    }

    @IsTest
    static void exactBoundaryDateIsCovered() {
        Date orderDate = Date.newInstance(2024, 1, 15);
        Date expiry = Date.newInstance(2025, 1, 15);
        System.assert(
            WarrantyService.isUnderWarranty(orderDate, 12, expiry),
            'The exact anniversary date must still be covered (inclusive boundary)'
        );
        System.assert(
            !WarrantyService.isUnderWarranty(orderDate, 12, expiry.addDays(1)),
            'The day after the anniversary must not be covered'
        );
    }

    @IsTest
    static void zeroMonthAndNullInputsAreNotCovered() {
        Date orderDate = Date.newInstance(2025, 1, 15);
        System.assert(!WarrantyService.isUnderWarranty(orderDate, 0, orderDate), 'Zero months means no coverage');
        System.assert(!WarrantyService.isUnderWarranty(null, 12, orderDate), 'Null order date means no coverage');
        System.assert(!WarrantyService.isUnderWarranty(orderDate, 12, null), 'Null request date means no coverage');
        System.assert(!WarrantyService.isUnderWarranty(orderDate, null, orderDate), 'Null months means no coverage');
    }

    @IsTest
    static void bulkEntitlementHandlesMissingAndPresentOrders() {
        Order_Record__c covered = new Order_Record__c(
            Order_Date__c = Date.today().addMonths(-1),
            Warranty_Months__c = 12,
            Customer_Email__c = 'covered@northwind.example',
            Amount__c = 240,
            Lifetime_Value__c = 900
        );
        insert covered;

        Support_Request__c withOrder = new Support_Request__c(
            Customer_Email__c = 'covered@northwind.example',
            Status__c = 'New',
            Channel__c = 'Web',
            Topic__c = 'Warranty',
            Related_Order__c = covered.Id
        );
        Support_Request__c withoutOrder = new Support_Request__c(
            Customer_Email__c = 'noorder@northwind.example',
            Status__c = 'New',
            Channel__c = 'Email',
            Topic__c = 'Warranty'
        );
        insert new List<Support_Request__c>{ withOrder, withoutOrder };

        Test.startTest();
        Map<Id, Boolean> verdicts = WarrantyService.checkEntitlement(new List<Support_Request__c>{ withOrder, withoutOrder });
        Test.stopTest();

        System.assertEquals(2, verdicts.size(), 'Both requests should be evaluated');
        System.assert(verdicts.get(withOrder.Id), 'The recent twelve-month order should be under warranty');
        System.assert(!verdicts.get(withoutOrder.Id), 'A request with no order cannot be under warranty');

        System.assert(
            WarrantyService.entitlementMessage(covered, Date.today()).containsIgnoreCase('warranty'),
            'The verdict message should mention warranty'
        );
    }
}
