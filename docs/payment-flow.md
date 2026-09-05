# Payment Flow

```
1. Buyer approves cart (or it's auto-ALLOWED under the approval threshold)
2. POST /payments/create
   - Loads the CheckoutIntent, refuses unless policy_decision == ALLOWED and buyer_approved == true
   - Creates (or finds existing) pending Order for this intent
   - Computes retry_count from prior PaymentAttempt rows for this intent
   - Re-runs the policy engine with the retry count -> BLOCKED if max_automatic_retries exceeded
   - idempotency_key = "{intent_id}:{attempt_number}" -> if this exact attempt already exists,
     returns it instead of creating a duplicate Razorpay order
   - Calls Razorpay order.create with amount in paise
   - Logs PAYMENT_CREATED
3. Frontend opens Razorpay Checkout.js with the returned order_id and key_id
4. Buyer completes (or cancels) the test payment in the Razorpay widget
5. POST /payments/verify with razorpay_order_id / payment_id / signature
   - verify_payment_signature() using the Razorpay Python SDK's utility method
   - On success: PaymentAttempt -> successful, Order -> paid/completed, PAYMENT_SUCCESS logged
   - On failure: PaymentAttempt -> failed, Order -> failed, PAYMENT_FAILED logged
```

## Failure handling (spec section 17)

If a payment fails and the buyer/agent tries again, `/payments/create` is called again for the
same `checkout_intent_id`. The retry count increments. Once `retry_count > max_automatic_retries`,
the policy engine returns `BLOCKED` with the reason:

> "Retry was not attempted because the configured retry limit has already been reached.
> No duplicate payment was created."

This is a 409 response, an audit `RETRY_BLOCKED` event, and no new Razorpay order is created.

## Never trust the frontend for financial state

- Checkout totals are recomputed server-side from the database on every `/checkout/intent` call.
- Payment amount sent to Razorpay comes from `CheckoutIntent.total`, not from any client-supplied
  amount field.
- Signature verification happens server-side via the Razorpay SDK before an order is ever marked
  paid.
