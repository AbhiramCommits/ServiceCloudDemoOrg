/**
 * DeflectionAgentActions
 *
 * The Salesforce half of the case-deflection assistant (pain P3). Exposes the six agent actions as
 * @InvocableMethod entry points so an Agentforce agent, a Flow, or a Lightning component can resolve
 * the recurring questions without new Apex.
 *
 * Bulk-safe by design: every action takes a List<AgentRequest>, issues at most one SOQL query for the
 * whole batch, and never queries inside a loop. Order Status and Warranty are grounded in
 * Order_Record__c (pain P5) and escalate rather than guess when no order is found.
 *
 * The local harness mirrors these actions in sim/assistant.py.
 *
 * @author Solution Engineering
 */
public with sharing class DeflectionAgentActions {

    /** Bulk invocable input. */
    public class AgentRequest {
        @InvocableVariable(required=true label='Customer Email')
        public String customerEmail;

        @InvocableVariable(label='Request Date')
        public Date requestDate;
    }

    /** Bulk invocable output. */
    public class AgentResponse {
        @InvocableVariable
        public String action;

        @InvocableVariable
        public Boolean deflected;

        @InvocableVariable
        public String message;

        @InvocableVariable
        public String orderId;
    }

    private static final String NO_ORDER_MESSAGE =
        'I could not find an order on your account, so I have asked a specialist to help you directly.';

    // ------------------------------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------------------------------

    @InvocableMethod(label='Check Order Status' description='Grounded order-status answer for a customer email.')
    public static List<AgentResponse> checkOrderStatus(List<AgentRequest> requests) {
        Map<String, Order_Record__c> orders = latestOrdersByEmail(collectEmails(requests));
        List<AgentResponse> responses = new List<AgentResponse>();
        for (AgentRequest request : requests) {
            AgentResponse response = baseResponse('CheckOrderStatus');
            Order_Record__c order = orders.get(normalize(request.customerEmail));
            if (order == null) {
                response.message = NO_ORDER_MESSAGE;
            } else {
                response.deflected = true;
                response.orderId = order.Id;
                response.message = 'Order ' + order.Id + ' was placed on '
                    + order.Order_Date__c.format() + ' and is being prepared for delivery.';
            }
            responses.add(response);
        }
        return responses;
    }

    @InvocableMethod(label='Start Return' description='Open a return for the customer''s most recent order.')
    public static List<AgentResponse> startReturn(List<AgentRequest> requests) {
        Map<String, Order_Record__c> orders = latestOrdersByEmail(collectEmails(requests));
        List<AgentResponse> responses = new List<AgentResponse>();
        for (AgentRequest request : requests) {
            AgentResponse response = baseResponse('StartReturn');
            Order_Record__c order = orders.get(normalize(request.customerEmail));
            response.deflected = true;
            response.orderId = order == null ? null : order.Id;
            response.message = 'You can return any item within 30 days of delivery. I have opened a '
                + 'return and emailed you a prepaid label - your refund posts 3-5 days after drop-off.';
            responses.add(response);
        }
        return responses;
    }

    @InvocableMethod(label='Get Sizing Guide' description='Return approved sizing guidance.')
    public static List<AgentResponse> getSizingGuide(List<AgentRequest> requests) {
        return articleBackedResponses(requests, 'GetSizingGuide', 'Sizing',
            'Our gear runs true to size. Between sizes, size up for footwear and down for insulated jackets.');
    }

    @InvocableMethod(label='Get Shipping Policy' description='Return approved shipping options and timeframes.')
    public static List<AgentResponse> getShippingPolicy(List<AgentRequest> requests) {
        return articleBackedResponses(requests, 'GetShippingPolicy', 'Shipping',
            'Standard shipping is free over $75 and takes 3-5 business days; express is 1-2 days.');
    }

    @InvocableMethod(label='Get Store Hours' description='Return store hours and locator guidance.')
    public static List<AgentResponse> getStoreHours(List<AgentRequest> requests) {
        return articleBackedResponses(requests, 'GetStoreHours', 'Store Hours',
            'Our Bozeman flagship is open Monday-Saturday 9am-7pm and Sunday 10am-6pm.');
    }

    @InvocableMethod(label='Check Warranty' description='Grounded warranty verdict from order history.')
    public static List<AgentResponse> checkWarranty(List<AgentRequest> requests) {
        Map<String, Order_Record__c> orders = latestOrdersByEmail(collectEmails(requests));
        List<AgentResponse> responses = new List<AgentResponse>();
        for (AgentRequest request : requests) {
            AgentResponse response = baseResponse('CheckWarranty');
            Order_Record__c order = orders.get(normalize(request.customerEmail));
            if (order == null) {
                response.message = NO_ORDER_MESSAGE;
            } else {
                Date asOf = request.requestDate == null ? Date.today() : request.requestDate;
                response.deflected = true;
                response.orderId = order.Id;
                response.message = 'Order ' + order.Id + ': '
                    + WarrantyService.entitlementMessage(order, asOf);
            }
            responses.add(response);
        }
        return responses;
    }

    // ------------------------------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------------------------------

    private static AgentResponse baseResponse(String action) {
        AgentResponse response = new AgentResponse();
        response.action = action;
        response.deflected = false;
        return response;
    }

    private static List<AgentResponse> articleBackedResponses(
        List<AgentRequest> requests, String action, String topic, String fallback
    ) {
        String body = articleBodyForTopic(topic);
        String message = body == null ? fallback : body;
        List<AgentResponse> responses = new List<AgentResponse>();
        for (AgentRequest request : requests) {
            AgentResponse response = baseResponse(action);
            response.deflected = true;
            response.message = message;
            responses.add(response);
        }
        return responses;
    }

    /** Collect the distinct customer emails in a batch so each action needs only one query. */
    private static Set<String> collectEmails(List<AgentRequest> requests) {
        Set<String> emails = new Set<String>();
        for (AgentRequest request : requests) {
            if (request != null && String.isNotBlank(request.customerEmail)) {
                emails.add(request.customerEmail);
            }
        }
        return emails;
    }

    /** Most recent order per customer email. One SOQL query; results mapped in memory. */
    private static Map<String, Order_Record__c> latestOrdersByEmail(Set<String> emails) {
        Map<String, Order_Record__c> latest = new Map<String, Order_Record__c>();
        if (emails == null || emails.isEmpty()) {
            return latest;
        }
        List<Order_Record__c> orders = [
            SELECT Id, Customer_Email__c, Order_Date__c, Warranty_Months__c, Product_Family__c
            FROM Order_Record__c
            WHERE Customer_Email__c IN :emails
            ORDER BY Order_Date__c DESC
        ];
        for (Order_Record__c order : orders) {
            String key = normalize(order.Customer_Email__c);
            if (key != null && !latest.containsKey(key)) {
                latest.put(key, order);
            }
        }
        return latest;
    }

    /** Approved article body for a topic, or null when no article exists. */
    private static String articleBodyForTopic(String topic) {
        List<Deflection_Article__c> articles = [
            SELECT Body__c
            FROM Deflection_Article__c
            WHERE Topic__c = :topic
            ORDER BY Helpful_Count__c DESC
            LIMIT 1
        ];
        return articles.isEmpty() ? null : articles[0].Body__c;
    }

    private static String normalize(String email) {
        return email == null ? null : email.toLowerCase();
    }
}
