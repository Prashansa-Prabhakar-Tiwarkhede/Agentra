import pytest
from app.policies.engine import evaluate_transaction, PolicyDecision


class FakePolicy:
    """Lightweight stand-in for the Policy ORM model, avoids needing a DB for these tests."""
    def __init__(
        self,
        max_transaction_amount=2000.0,
        approval_threshold=1000.0,
        max_automatic_retries=1,
        max_discount_percent=10.0,
        max_upsell_amount=200.0,
    ):
        self.max_transaction_amount = max_transaction_amount
        self.approval_threshold = approval_threshold
        self.max_automatic_retries = max_automatic_retries
        self.max_discount_percent = max_discount_percent
        self.max_upsell_amount = max_upsell_amount


def test_allowed_within_all_limits():
    result = evaluate_transaction(policy=FakePolicy(), total_amount=800, buyer_budget=1500)
    assert result.decision == PolicyDecision.ALLOWED


def test_spec_example_gift_box_allowed():
    # From spec section 14: product 1299 + wrap 149 = 1448, max allowed 1500 -> ALLOWED
    # approval_threshold is raised here to isolate the "within budget" example
    result = evaluate_transaction(
        policy=FakePolicy(approval_threshold=1500, max_transaction_amount=2000),
        total_amount=1448,
        buyer_budget=1500,
    )
    assert result.decision == PolicyDecision.ALLOWED


def test_spec_example_requires_approval():
    # product 1499 + upsell 299 = 1798, approval_threshold 1500 -> REQUIRES_APPROVAL
    result = evaluate_transaction(
        policy=FakePolicy(approval_threshold=1500, max_transaction_amount=2000, max_upsell_amount=300),
        total_amount=1798,
        upsell_amount=299,
    )
    assert result.decision == PolicyDecision.REQUIRES_APPROVAL


def test_blocked_exceeds_hard_cap():
    result = evaluate_transaction(policy=FakePolicy(max_transaction_amount=2000), total_amount=2500)
    assert result.decision == PolicyDecision.BLOCKED
    assert "maximum allowed transaction amount" in result.reason


def test_blocked_exceeds_buyer_budget():
    result = evaluate_transaction(policy=FakePolicy(), total_amount=1600, buyer_budget=1500)
    assert result.decision == PolicyDecision.BLOCKED
    assert "buyer's stated budget" in result.reason


def test_blocked_upsell_over_limit():
    result = evaluate_transaction(
        policy=FakePolicy(max_upsell_amount=200), total_amount=1000, upsell_amount=250
    )
    assert result.decision == PolicyDecision.BLOCKED
    assert "upsell" in result.reason


def test_blocked_discount_over_limit():
    result = evaluate_transaction(
        policy=FakePolicy(max_discount_percent=10), total_amount=900, discount_percent=25
    )
    assert result.decision == PolicyDecision.BLOCKED
    assert "Discount" in result.reason


def test_requires_approval_over_threshold():
    result = evaluate_transaction(policy=FakePolicy(approval_threshold=1000), total_amount=1200)
    assert result.decision == PolicyDecision.REQUIRES_APPROVAL


def test_allowed_after_buyer_approval_even_above_threshold():
    result = evaluate_transaction(
        policy=FakePolicy(approval_threshold=1000),
        total_amount=1200,
        already_buyer_approved=True,
    )
    assert result.decision == PolicyDecision.ALLOWED


def test_retry_blocked_when_limit_reached():
    result = evaluate_transaction(
        policy=FakePolicy(max_automatic_retries=1), total_amount=500, retry_count=2
    )
    assert result.decision == PolicyDecision.BLOCKED
    assert "retry limit" in result.reason.lower()


def test_retry_allowed_within_limit():
    result = evaluate_transaction(
        policy=FakePolicy(max_automatic_retries=1, approval_threshold=1000), total_amount=500, retry_count=1
    )
    assert result.decision == PolicyDecision.ALLOWED


def test_checks_list_is_populated_for_explainability():
    result = evaluate_transaction(policy=FakePolicy(), total_amount=500)
    assert len(result.checks) >= 1
    assert all("check" in c and "passed" in c and "detail" in c for c in result.checks)
