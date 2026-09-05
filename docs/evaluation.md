# Evaluation Notes (Track 01 criteria)

| Requirement | Where it's implemented |
|---|---|
| Explainable | Every `AuditEvent` has a `reason`. Policy decisions include a per-check trace (`PolicyResult.checks`). |
| Bounded | `Policy` model: max transaction, approval threshold, max retries, max discount, max upsell — all merchant-configurable. |
| Gated | `app/policies/engine.py` — every checkout and every payment attempt is evaluated before proceeding. |
| Auditable | `app/audit/logger.py` — single write path, `audit_events` table, `/dashboard/audit` UI. |
| Graceful failure | Simulated payment decline -> retry policy check -> `RETRY_BLOCKED` -> explained to buyer -> audited. Also: AI provider failure -> `AI_ERROR` audited, buyer gets a calm message, no crash. |
| LLM never executes payment | `app/payments/` is never imported by `app/agents/`. Verified by code inspection and by the fact `tools.py`'s `TOOL_REGISTRY` has no payment function. |

## What's been tested, not just written

- `backend/tests/test_policy_engine.py`: 12/12 passing, includes both worked examples from the
  original spec (₹1448 -> ALLOWED, ₹1798 -> REQUIRES_APPROVAL) and every decision branch.
- End-to-end smoke test (merchant creation -> product creation -> checkout intent -> policy
  decision -> audit log) run against a live FastAPI TestClient, not just unit-level.
- Seed script produces 31 products and four scripted scenarios (success / approval-required /
  blocked / payment-failure), verified against the real `/analytics/summary` and `/audit`
  endpoints.
- Frontend: `tsc -b` clean compile and `vite build` production build both verified after every
  major addition.

## What still needs a real judge-facing dry run

- Actual Razorpay TEST MODE keys have not been exercised yet (needs your dashboard keys).
- Actual Groq API key has not been exercised yet — the graceful `AI_UNAVAILABLE` path has been
  verified instead, which is itself part of the "handle failure gracefully" requirement.
