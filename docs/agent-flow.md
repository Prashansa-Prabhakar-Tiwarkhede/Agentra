# Agent Flow

## Two LLM calls per buyer turn, never more, never fewer

1. **Intent parsing** (`INTENT_SYSTEM_PROMPT` in `app/agents/agent.py`)
   Input: raw buyer message.
   Output: structured JSON — occasion, recipient, maximum_budget, category, query_text, tags.
   The model has no tool access at this stage; it's pure extraction.

2. **Recommendation** (`RECOMMEND_SYSTEM_PROMPT`)
   Input: the parsed intent + a pre-filtered, backend-priced candidate list (max 5 products,
   already matched against budget/category/tags by `tools.search_products`).
   Output: a reply, a `recommended_product_id` (must be one of the candidates — validated before
   use), a confidence score, and an optional upsell suggestion (also validated against the
   product's real `upsell_product_ids` before being surfaced).

## What happens on AI failure

`GroqProvider.complete_json` never raises. A network error, timeout, rate limit, or malformed
JSON response all become `{"error": "...", "detail": "..."}`. `run_buyer_turn` checks for this
and returns a calm, generic buyer-facing message plus an `AI_ERROR` audit event — never a stack
trace, never a hang.

## What the frontend receives

```
{
  "session_id": "...",
  "reply": "The Premium Gift Box is a great fit at Rs 1299. Want gift wrapping for Rs 149?",
  "structured_action": {
    "action": "RECOMMEND_PRODUCT",
    "product_id": "...",
    "reason": "...",
    "confidence": 0.92
  },
  "products": [ "up to 5 candidates, AI-safe fields only" ]
}
```

The frontend never receives a payment instruction from this endpoint — `structured_action.action`
is always `RECOMMEND_PRODUCT` or absent. Checkout is a separate, explicit buyer action
(clicking "Add" then "Review checkout").
