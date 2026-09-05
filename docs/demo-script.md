# Demo Script

**Total time: ~4 minutes**

1. **Landing page** (15s) — "Commerce built for the age of AI buyers." Point out the live audit
   ledger preview — this is the product's actual thesis, not decoration.

2. **Buyer chat** (60s) — Open `/buyer/<merchant-id>`. Type:
   *"I need a birthday gift for my friend under ₹1500."*
   Agent recommends the Premium Gift Box, offers gift wrap upsell. Add both to cart, review
   checkout — show the policy panel: total ₹1448, `ALLOWED`, reason shown inline.

3. **Razorpay test payment** (30s) — Click "Pay with Razorpay (Test Mode)". Use Razorpay's test
   card (4111 1111 1111 1111, any future expiry, any CVV). Show the success state.

4. **Approval-required scenario** (45s) — New session, request something pricier that crosses
   the approval threshold. Show the `REQUIRES_APPROVAL` pill and reason, click "Approve
   Purchase," show it flip to `ALLOWED`.

5. **Blocked scenario** (30s) — Request something over the hard cap. Show `BLOCKED`, no payment
   option offered.

6. **Payment failure** (30s, if using Razorpay's test failure card) — Show the graceful
   `RETRY_BLOCKED` message on a second attempt.

7. **Merchant dashboard** (60s) — `/dashboard/audit`: scroll through every event from the last
   four minutes, timestamped, reasoned, decision-tagged. `/dashboard` overview: AI GMV,
   conversion, upsells. `/dashboard/playground`: run the same buyer request, show the structured
   action JSON — "this is what actually drove the recommendation, not a black box."

8. **Close** — "Every one of those decisions was made by a policy engine that has never touched
   an LLM call. The AI recommends; it never authorizes."
