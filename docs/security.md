# Security Considerations

- **Secrets**: all API keys (Groq, Razorpay, Supabase) load from environment variables via
  `app/config.py`. Nothing is hardcoded. The frontend never receives `RAZORPAY_KEY_SECRET` —
  only the public `RAZORPAY_KEY_ID`, returned by `/payments/create` at the moment a payment is
  actually being initiated.
- **Auth**: Supabase-issued JWTs are verified server-side in `app/auth.py` using the shared
  `SUPABASE_JWT_SECRET`. The backend never handles raw passwords.
- **No arbitrary LLM execution**: the agent can only call functions explicitly listed in
  `app/agents/tools.py`. There is no code-execution tool, no raw-SQL tool, no filesystem tool.
- **No direct LLM payment access**: `app/payments/` is never imported by `app/agents/`. The only
  path from an AI recommendation to money moving is through the Checkout API and Policy Engine.
- **Server-side pricing**: every checkout total is recomputed from the database
  (`tools.calculate_cart`), never trusted from the AI's stated price or the frontend's cached price.
- **Idempotency**: `PaymentAttempt.idempotency_key` prevents duplicate Razorpay orders for the
  same logical attempt.
- **Signature verification**: payments are only marked successful after server-side verification
  via the Razorpay SDK's `verify_payment_signature`.
- **Generic error responses**: the global FastAPI exception handler in `app/main.py` returns a
  fixed generic message for unhandled exceptions — no stack traces reach the client.
- **CORS**: restricted to `CORS_ORIGINS` from environment config, not wildcarded in production.

## Closed gaps

- **Rate limiting**: `slowapi` is wired in (`app/rate_limit.py`), applied to `/agent/chat`
  (20/minute per IP) and `/payments/create` (10/minute per IP) — the two endpoints that cost
  API spend or touch money. Verified: the 21st request within a minute returns `429`.
- **Supabase RLS**: `database/rls_policies.sql` enables Row Level Security on every table and
  scopes access to the owning merchant (`auth.uid()` matched against `merchants.auth_user_id`).
  Run it once in the Supabase SQL Editor. Note: the backend connects with the database owner/
  service role credentials and bypasses RLS regardless — this is defense-in-depth for any future
  direct-from-frontend Supabase queries, not a fix for an active vulnerability in this build.

## Known gaps (hackathon scope)

- No webhook signature verification for async Razorpay events (this build verifies synchronously
  via the client-side handler instead).
- Rate limiting is keyed by client IP, which is naive behind a load balancer/proxy in production
  (would need to read a forwarded-for header or key off authenticated session instead).
