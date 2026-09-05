"""
Agent orchestrator.

Flow enforced here (matches the spec's architecture invariant):
    buyer message -> AI parses intent (structured JSON, no tool access)
    -> orchestrator calls explicit tools itself (search_products, calculate_cart, ...)
    -> AI is given ONLY the tool results and asked to recommend + explain
    -> orchestrator returns a structured_action the frontend/checkout API can act on
    -> the LLM never sees a payment tool and never triggers one directly.
"""
from sqlalchemy.orm import Session

from app.agents import tools
from app.audit.logger import log_event
from app.models.merchant import Merchant, AgentConfig
from app.models.session import AgentSession, AgentMessage
from app.services.ai_provider import get_ai_provider

INTENT_SYSTEM_PROMPT = """You are an intent parser for an e-commerce AI shopping assistant.
Given a buyer's message, extract structured shopping intent as JSON with these fields:
{
  "occasion": string or null,
  "recipient": string or null,
  "maximum_budget": number or null,
  "category": string or null,
  "query_text": string,   // short free-text search phrase capturing what they want
  "tags": [string]        // relevant tags, lowercase
}
Return ONLY the JSON object, no other text."""

RECOMMEND_SYSTEM_PROMPT = """You are a helpful, concise AI shopping assistant for an online store.
You are given the buyer's parsed intent and a list of candidate products (already filtered
and priced by the backend - these are the ONLY products you may recommend or mention).
Respond with JSON:
{
  "reply": string,                     // natural, friendly reply to show the buyer
  "recommended_product_id": string or null,
  "reason": string,                    // human-readable why this product fits (used in audit trail)
  "confidence": number,                // 0-1
  "suggest_upsell_product_id": string or null,
  "upsell_reply": string or null,      // e.g. "Would you like gift wrapping for ₹149?"
  "suggest_cross_sell_product_id": string or null,
  "cross_sell_reply": string or null   // e.g. "Pairs well with our wireless charger — want to add it?"
}
Only recommend a product_id that appears in the candidate list. If nothing fits, set
recommended_product_id to null and explain why in reply. Return ONLY the JSON object."""


def _get_or_create_session(db: Session, merchant_id: str, session_id: str | None) -> AgentSession:
    if session_id:
        existing = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if existing:
            return existing
    session = AgentSession(merchant_id=merchant_id, status="active")
    db.add(session)
    db.commit()
    db.refresh(session)
    log_event(
        db, merchant_id=merchant_id, session_id=session.id,
        event_type="AI_SESSION_STARTED", actor="system", result="success",
    )
    return session


def run_buyer_turn(db: Session, *, merchant: Merchant, session_id: str | None, message: str,
                    buyer_budget_override: float | None = None) -> dict:
    ai = get_ai_provider()
    session = _get_or_create_session(db, merchant.id, session_id)

    db.add(AgentMessage(session_id=session.id, role="buyer", content=message))
    db.commit()

    # 1. Parse intent (LLM call #1 — no tool access, pure extraction)
    intent = ai.complete_json(INTENT_SYSTEM_PROMPT, message)
    if intent.get("error"):
        reply = "I'm having trouble understanding requests right now — please try again in a moment."
        log_event(db, merchant_id=merchant.id, session_id=session.id, event_type="AI_ERROR",
                  actor="system", reason=intent.get("detail"), result="failure")
        return {"session_id": session.id, "reply": reply, "structured_action": None, "products": []}

    if buyer_budget_override is not None:
        intent["maximum_budget"] = buyer_budget_override

    log_event(
        db, merchant_id=merchant.id, session_id=session.id, event_type="PRODUCT_SEARCH",
        actor="agent", reason=f"Buyer request: {message}", input_data=intent, result="success",
    )

    # 2. Backend-controlled tool call — the LLM never queries the DB itself.
    # The AI's free-form category/tags rarely match the merchant's exact catalog taxonomy
    # (e.g. it says "Birthday Gifts", the DB category is "Gifts"), so a single strict-filter
    # search can wrongly return zero results even when plenty of products fit the budget.
    # Progressively relax non-price filters rather than giving up after one attempt.
    search_kwargs_attempts = [
        {"category": intent.get("category"), "tags": intent.get("tags") or None, "query_text": intent.get("query_text")},
        {"category": None, "tags": intent.get("tags") or None, "query_text": intent.get("query_text")},
        {"category": None, "tags": None, "query_text": intent.get("query_text")},
        {"category": None, "tags": None, "query_text": None},
    ]
    candidates: list[dict] = []
    for extra in search_kwargs_attempts:
        candidates = tools.search_products(
            db, merchant.id,
            max_price=intent.get("maximum_budget"),
            limit=5,
            **extra,
        )
        if candidates:
            break

    if not candidates:
        reply = "I couldn't find anything matching that in the catalog right now — want to try a different budget or category?"
        db.add(AgentMessage(session_id=session.id, role="agent", content=reply))
        db.commit()
        return {"session_id": session.id, "reply": reply, "structured_action": None, "products": []}

    # 3. Recommendation (LLM call #2 — sees only the pre-filtered, backend-priced candidates)
    agent_cfg = merchant.agent_config or AgentConfig()
    rec_prompt = (
        f"Buyer intent: {intent}\n"
        f"Agent personality: {agent_cfg.personality}\n"
        f"Candidate products (ONLY these may be recommended): {candidates}"
    )
    rec = ai.complete_json(RECOMMEND_SYSTEM_PROMPT, rec_prompt)

    if rec.get("error"):
        reply = f"Here's what I found: {', '.join(c['name'] for c in candidates[:3])}."
        db.add(AgentMessage(session_id=session.id, role="agent", content=reply))
        db.commit()
        return {"session_id": session.id, "reply": reply, "structured_action": None, "products": candidates}

    recommended_id = rec.get("recommended_product_id")
    structured_action = None
    upsell_reply_text = None
    cross_sell_reply_text = None
    if recommended_id and any(c["product_id"] == recommended_id for c in candidates):
        structured_action = {
            "action": "RECOMMEND_PRODUCT",
            "product_id": recommended_id,
            "reason": rec.get("reason"),
            "confidence": rec.get("confidence"),
        }
        log_event(
            db, merchant_id=merchant.id, session_id=session.id, event_type="PRODUCT_RECOMMENDED",
            actor="agent", reason=rec.get("reason"), output_data=structured_action, result="success",
        )

        # Upsell — only if enabled, only from real catalog relationships. If disabled, or the
        # AI's suggested product isn't a genuine upsell relationship for this item, the upsell
        # text is dropped entirely — it never reaches the buyer just because the model said it.
        upsell_id = rec.get("suggest_upsell_product_id")
        if agent_cfg.upselling_enabled and upsell_id:
            upsell_candidates = tools.get_upsell_candidates(db, merchant.id, recommended_id)
            if any(u["product_id"] == upsell_id for u in upsell_candidates):
                upsell_reply_text = rec.get("upsell_reply")
                log_event(
                    db, merchant_id=merchant.id, session_id=session.id, event_type="UPSELL_SUGGESTED",
                    actor="agent", reason=upsell_reply_text,
                    output_data={"upsell_product_id": upsell_id}, result="success",
                )

        # Cross-sell — same validated-suggestion pattern as upsell, but drawing from
        # cross_sell_product_ids (complementary products) instead of upsell_product_ids
        # (add-ons to the same item).
        cross_sell_id = rec.get("suggest_cross_sell_product_id")
        if agent_cfg.cross_selling_enabled and cross_sell_id:
            cross_sell_candidates = tools.get_cross_sell_candidates(db, merchant.id, recommended_id)
            if any(c["product_id"] == cross_sell_id for c in cross_sell_candidates):
                cross_sell_reply_text = rec.get("cross_sell_reply")
                log_event(
                    db, merchant_id=merchant.id, session_id=session.id, event_type="CROSS_SELL_SUGGESTED",
                    actor="agent", reason=cross_sell_reply_text,
                    output_data={"cross_sell_product_id": cross_sell_id}, result="success",
                )

    reply_text = rec.get("reply", "")
    if upsell_reply_text:
        reply_text = f"{reply_text} {upsell_reply_text}"
    if cross_sell_reply_text:
        reply_text = f"{reply_text} {cross_sell_reply_text}"

    db.add(AgentMessage(session_id=session.id, role="agent", content=reply_text, structured_action=structured_action))
    db.commit()

    return {
        "session_id": session.id,
        "reply": reply_text,
        "structured_action": structured_action,
        "products": candidates,
    }
