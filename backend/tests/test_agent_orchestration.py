"""
Tests the orchestration logic in app/agents/agent.py against a scripted fake AI provider,
so the recommendation/upsell VALIDATION logic (the part that matters for safety) is verified
without needing a real Groq key or non-deterministic real model output.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.merchant import Merchant, AgentConfig, Policy
from app.models.product import Product
from app.models.audit import AuditEvent
import app.agents.agent as agent_module


class FakeProvider:
    """Returns pre-scripted responses in call order, ignoring the actual prompt content."""
    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.calls = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        if not self._responses:
            return {"error": "AI_UNAVAILABLE", "detail": "no more scripted responses"}
        return self._responses.pop(0)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def merchant(db_session):
    m = Merchant(auth_user_id="u1", business_name="Test Store", onboarding_complete=True)
    db_session.add(m)
    db_session.flush()
    cfg = AgentConfig(merchant_id=m.id, upselling_enabled=True, cross_selling_enabled=True)
    db_session.add(cfg)
    db_session.add(Policy(merchant_id=m.id))
    gift = Product(merchant_id=m.id, name="Gift Box", category="Gifts", price=1299, inventory=10, tags=["birthday"])
    wrap = Product(merchant_id=m.id, name="Gift Wrap", category="Add-on", price=149, inventory=50)
    card = Product(merchant_id=m.id, name="Greeting Card", category="Gifts", price=99, inventory=20)
    unrelated = Product(merchant_id=m.id, name="Random Widget", category="Other", price=99, inventory=5)
    db_session.add_all([gift, wrap, card, unrelated])
    db_session.flush()
    gift.upsell_product_ids = [wrap.id]
    gift.cross_sell_product_ids = [card.id]
    db_session.commit()
    db_session.refresh(m)
    return {"merchant": m, "gift": gift, "wrap": wrap, "card": card, "unrelated": unrelated}


def set_fake_provider(monkeypatch, responses):
    provider = FakeProvider(responses)
    monkeypatch.setattr(agent_module, "get_ai_provider", lambda: provider)
    return provider


def test_happy_path_recommendation_and_valid_upsell(db_session, merchant, monkeypatch):
    gift, wrap = merchant["gift"], merchant["wrap"]
    set_fake_provider(monkeypatch, [
        {"occasion": "birthday", "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": ["birthday"]},
        {
            "reply": "The Gift Box is perfect.",
            "recommended_product_id": gift.id,
            "reason": "Matches occasion and budget.",
            "confidence": 0.9,
            "suggest_upsell_product_id": wrap.id,
            "upsell_reply": "Want gift wrapping for 149 rupees?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="birthday gift under 1500"
    )
    assert result["structured_action"]["product_id"] == gift.id
    assert "Want gift wrapping" in result["reply"]

    events = db_session.query(AuditEvent).all()
    types = [e.event_type for e in events]
    assert "PRODUCT_RECOMMENDED" in types
    assert "UPSELL_SUGGESTED" in types


def test_invalid_recommended_product_id_is_rejected(db_session, merchant, monkeypatch):
    """AI hallucinates a product_id that was never in the candidate list — must not be trusted."""
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": []},
        {
            "reply": "Here's something great.",
            "recommended_product_id": "totally-made-up-id-not-in-catalog",
            "reason": "hallucinated",
            "confidence": 0.99,
            "suggest_upsell_product_id": None,
            "upsell_reply": None,
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="gift"
    )
    assert result["structured_action"] is None
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "PRODUCT_RECOMMENDED").all()
    assert events == []


def test_invalid_upsell_relationship_never_reaches_buyer(db_session, merchant, monkeypatch):
    """AI suggests upselling a product with no real upsell_product_ids link — must be dropped
    both from the audit log AND from the buyer-facing reply text."""
    gift, unrelated = merchant["gift"], merchant["unrelated"]
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": []},
        {
            "reply": "The Gift Box works well.",
            "recommended_product_id": gift.id,
            "reason": "fits",
            "confidence": 0.8,
            "suggest_upsell_product_id": unrelated.id,  # NOT a real upsell relationship for gift
            "upsell_reply": "Also grab this random widget for 99 rupees?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="gift"
    )
    assert "random widget" not in result["reply"].lower()
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "UPSELL_SUGGESTED").all()
    assert events == []


def test_upselling_disabled_suppresses_upsell_text_even_if_ai_suggests_it(db_session, merchant, monkeypatch):
    """Regression test for a real bug: upselling_enabled=False must fully suppress upsell text,
    not just skip the audit log entry."""
    merchant["merchant"].agent_config.upselling_enabled = False
    db_session.commit()
    gift, wrap = merchant["gift"], merchant["wrap"]
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": []},
        {
            "reply": "The Gift Box works well.",
            "recommended_product_id": gift.id,
            "reason": "fits",
            "confidence": 0.8,
            "suggest_upsell_product_id": wrap.id,  # valid relationship, but upselling is OFF
            "upsell_reply": "Want gift wrapping for 149 rupees?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="gift"
    )
    assert "gift wrapping" not in result["reply"].lower()
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "UPSELL_SUGGESTED").all()
    assert events == []


def test_valid_cross_sell_is_surfaced(db_session, merchant, monkeypatch):
    gift, card = merchant["gift"], merchant["card"]
    set_fake_provider(monkeypatch, [
        {"occasion": "birthday", "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": ["birthday"]},
        {
            "reply": "The Gift Box is perfect.",
            "recommended_product_id": gift.id,
            "reason": "Matches occasion and budget.",
            "confidence": 0.9,
            "suggest_upsell_product_id": None,
            "upsell_reply": None,
            "suggest_cross_sell_product_id": card.id,
            "cross_sell_reply": "Pairs nicely with a greeting card too?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="birthday gift"
    )
    assert "greeting card" in result["reply"].lower()
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "CROSS_SELL_SUGGESTED").all()
    assert len(events) == 1


def test_invalid_cross_sell_relationship_never_reaches_buyer(db_session, merchant, monkeypatch):
    gift, unrelated = merchant["gift"], merchant["unrelated"]
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": []},
        {
            "reply": "The Gift Box works well.",
            "recommended_product_id": gift.id,
            "reason": "fits",
            "confidence": 0.8,
            "suggest_upsell_product_id": None,
            "upsell_reply": None,
            "suggest_cross_sell_product_id": unrelated.id,  # NOT a real cross-sell link
            "cross_sell_reply": "Also grab this random widget?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="gift"
    )
    assert "random widget" not in result["reply"].lower()
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "CROSS_SELL_SUGGESTED").all()
    assert events == []


def test_cross_selling_disabled_suppresses_text_even_if_ai_suggests_it(db_session, merchant, monkeypatch):
    merchant["merchant"].agent_config.cross_selling_enabled = False
    db_session.commit()
    gift, card = merchant["gift"], merchant["card"]
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": []},
        {
            "reply": "The Gift Box works well.",
            "recommended_product_id": gift.id,
            "reason": "fits",
            "confidence": 0.8,
            "suggest_upsell_product_id": None,
            "upsell_reply": None,
            "suggest_cross_sell_product_id": card.id,  # valid relationship, but cross-selling is OFF
            "cross_sell_reply": "Pairs nicely with a greeting card too?",
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="gift"
    )
    assert "greeting card" not in result["reply"].lower()
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "CROSS_SELL_SUGGESTED").all()
    assert events == []


def test_intent_parse_failure_degrades_gracefully(db_session, merchant, monkeypatch):
    set_fake_provider(monkeypatch, [
        {"error": "AI_UNAVAILABLE", "detail": "network timeout"},
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="anything"
    )
    assert result["structured_action"] is None
    assert result["products"] == []
    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "AI_ERROR").all()
    assert len(events) == 1
    assert events[0].reason == "network timeout"


def test_no_matching_candidates_returns_helpful_fallback(db_session, merchant, monkeypatch):
    set_fake_provider(monkeypatch, [
        {"occasion": None, "maximum_budget": 5, "category": None, "query_text": "nothing at this price", "tags": []},
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="something cheap"
    )
    assert result["structured_action"] is None
    assert "couldn't find" in result["reply"].lower()


def test_category_mismatch_falls_back_to_broader_search(db_session, merchant, monkeypatch):
    """Regression test for a real bug seen in practice: the AI's free-form category/tags
    ("Birthday Gifts", "birthday gift for friend") rarely match the merchant's exact catalog
    taxonomy ("Gifts"), which used to zero out every result even when products clearly fit
    the budget. The search must progressively relax filters instead of giving up immediately."""
    set_fake_provider(monkeypatch, [
        {
            "occasion": "birthday", "maximum_budget": 3500,
            "category": "Birthday Gifts",  # doesn't match the seeded "Gifts" category
            "query_text": "birthday gift for my friend",  # won't literally appear in any product name
            "tags": ["birthday gift for friend"],  # won't match single-word product tags either
        },
        {
            "reply": "The Gift Box is a great fit.",
            "recommended_product_id": merchant["gift"].id,
            "reason": "fits budget",
            "confidence": 0.85,
            "suggest_upsell_product_id": None,
            "upsell_reply": None,
        },
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None,
        message="I need a birthday gift for my friend under ₹3500."
    )
    assert len(result["products"]) > 0
    assert result["structured_action"] is not None
    assert result["structured_action"]["product_id"] == merchant["gift"].id


def test_recommendation_call_failure_still_shows_candidates(db_session, merchant, monkeypatch):
    set_fake_provider(monkeypatch, [
        {"occasion": "birthday", "maximum_budget": 1500, "category": None, "query_text": "gift", "tags": ["birthday"]},
        {"error": "AI_MALFORMED_RESPONSE", "detail": "not json"},
    ])
    result = agent_module.run_buyer_turn(
        db_session, merchant=merchant["merchant"], session_id=None, message="birthday gift"
    )
    assert result["structured_action"] is None
    assert len(result["products"]) >= 1
    assert "Gift Box" in result["reply"]
