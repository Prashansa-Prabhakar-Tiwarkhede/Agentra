# Architecture

## Layering

```
frontend (React)
   |
   v
backend/app/api/*        <- HTTP boundary, auth, request/response schemas
   |
   +--> app/agents/*      <- LLM orchestration, intent parsing, structured actions
   |        |
   |        v
   |     app/agents/tools.py   <- explicit, validated DB reads. No payment access.
   |
   +--> app/policies/engine.py <- pure function, no DB/LLM. ALLOWED/REQUIRES_APPROVAL/BLOCKED.
   |
   +--> app/payments/*    <- ONLY module that imports the Razorpay SDK
   |
   +--> app/audit/logger.py    <- single write path for every audit_events row
   |
   v
app/models/*  (SQLAlchemy) <-> Postgres (Supabase) / SQLite (local dev)
```

## Why the policy engine is isolated

`app/policies/engine.py` has no import of SQLAlchemy, FastAPI, or any AI SDK. It's a pure
function: `Policy-like config + transaction numbers -> PolicyResult`. This makes it:

- Trivially unit-testable (`backend/tests/test_policy_engine.py`, 12 cases, no DB fixture needed)
- Auditable by a judge or a security reviewer without needing to trace through the LLM layer
- Reusable for both the initial checkout decision and the retry-blocking decision — the same
  function gates both

## Why the LLM never sees the database directly

`app/agents/agent.py` calls functions in `app/agents/tools.py`, never raw SQL or ORM queries.
Each tool function validates its own inputs and returns only `Product.to_ai_context()` —
a deliberately narrow view (no merchant internals, no other buyers' data). The LLM is given the
*results* of tool calls, never the ability to invoke arbitrary ones.

## Why checkout totals are always re-priced server-side

`app/api/checkout.py` calls `tools.calculate_cart()`, which re-reads each product's price from
the database by ID. The price the AI mentioned in conversation, or that the frontend cached, is
never trusted for the actual `CheckoutIntent.total` that the policy engine evaluates.

## Idempotency

`PaymentAttempt.idempotency_key` is `{checkout_intent_id}:{attempt_number}`. A repeated request
for the same attempt number returns the existing row instead of creating a new Razorpay order.
Retry attempts increment the number and are separately policy-checked against
`max_automatic_retries` before a new Razorpay order is ever created.
