/**
 * WarrantyService
 *
 * Replaces Northwind's manual "open the store admin and count the months on your fingers" warranty
 * check (pain P5). Pure date math plus a bulk, SOQL-driven entitlement evaluation over order history.
 *
 * The date logic is mirrored by sim/warranty.py so the harness and the org agree on eligibility.
 *
 * Bulk-safety: the entitlement check issues exactly one SOQL query for the whole batch and never
 * queries inside a loop.
 *
 * @author Solution Engineering
 */
public with sharing class WarrantyService {

    /**
     * Is the request date within the warranty window of the order date?
     *
     * The window is inclusive of the exact boundary: an order placed 12 months ago with a 12-month
     * warranty is still covered on the anniversary date.
     *
     * @param orderDate      the date the order was placed
     * @param warrantyMonths the number of months of coverage (0 or null means no coverage)
     * @param requestDate    the date the customer is asking
     * @return true if still under warranty
     */
    public static Boolean isUnderWarranty(Date orderDate, Integer warrantyMonths, Date requestDate) {
        if (orderDate == null || requestDate == null) {
            return false;
        }
        if (warrantyMonths == null || warrantyMonths <= 0) {
            return false;
        }
        Date expiry = orderDate.addMonths(warrantyMonths);
        return !requestDate.isAfter(expiry);
    }

    /**
     * Bulk entitlement check for a set of requests, keyed by request Id.
     *
     * One SOQL query for the whole batch. Requests without a related order, or whose order has no
     * warranty, evaluate to false.
     *
     * @param requests the support requests to evaluate (Related_Order__c is read, CreatedDate is used
     *                 as the request date; a null CreatedDate falls back to today)
     * @return map of request Id -> eligibility
     */
    public static Map<Id, Boolean> checkEntitlement(List<Support_Request__c> requests) {
        Map<Id, Boolean> verdicts = new Map<Id, Boolean>();
        if (requests == null || requests.isEmpty()) {
            return verdicts;
        }

        Set<Id> orderIds = new Set<Id>();
        for (Support_Request__c req : requests) {
            if (req.Related_Order__c != null) {
                orderIds.add(req.Related_Order__c);
            }
        }

        Map<Id, Order_Record__c> orders = new Map<Id, Order_Record__c>();
        if (!orderIds.isEmpty()) {
            List<Order_Record__c> queried = [
                SELECT Id, Order_Date__c, Warranty_Months__c
                FROM Order_Record__c
                WHERE Id IN :orderIds
            ];
            orders.putAll(queried);
        }

        for (Support_Request__c req : requests) {
            Order_Record__c order = req.Related_Order__c == null ? null : orders.get(req.Related_Order__c);
            if (order == null) {
                verdicts.put(req.Id, false);
                continue;
            }
            Date requestDate = req.CreatedDate == null ? Date.today() : req.CreatedDate.date();
            verdicts.put(req.Id, isUnderWarranty(order.Order_Date__c, (Integer) order.Warranty_Months__c, requestDate));
        }
        return verdicts;
    }

    /**
     * Human-readable entitlement verdict for a single order, suitable for the deflection assistant's
     * response text and the Warranty_Eligibility_Check flow.
     */
    public static String entitlementMessage(Order_Record__c order, Date requestDate) {
        if (order == null) {
            return 'We could not find that order on your account. A specialist will follow up.';
        }
        Integer months = (Integer) order.Warranty_Months__c;
        if (isUnderWarranty(order.Order_Date__c, months, requestDate)) {
            Date expiry = order.Order_Date__c.addMonths(months);
            return 'Good news - this purchase is still under warranty through '
                + expiry.format()
                + '. We can start a warranty claim for you.';
        }
        return 'Your warranty window has ended. We can still help - here is our out-of-warranty repair option.';
    }
}
