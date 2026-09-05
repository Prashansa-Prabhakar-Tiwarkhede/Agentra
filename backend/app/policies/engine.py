"""
Guardrail Engine.

This module is intentionally pure Python with zero LLM involvement.
It takes a proposed transaction + a merchant's Policy config and returns
a deterministic decision. The agent can SUGGEST a purchase; only this
engine (via the checkout API) can say whether it's allowed to proceed.

Architecture invariant enforced by the whole codebase:
    LLM -> structured action -> validation -> POLICY ENGINE -> permission check
    -> backend action -> Razorpay
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol


class PolicyLike(Protocol):
    """
    Structural type so the engine can be unit-tested with a plain object
    (no DB/ORM needed) while still type-checking against the real Policy model.
    """
    max_transaction_amount: float
    approval_threshold: float
    max_automatic_retries: int
    max_discount_percent: float
    max_upsell_amount: float


if TYPE_CHECKING:
    from app.models.merchant import Policy


class PolicyDecision(str, Enum):
    ALLOWED = "ALLOWED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str
    checks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "checks": self.checks,
        }


def evaluate_transaction(
    *,
    policy: "Policy | PolicyLike",
    total_amount: float,
    buyer_budget: float | None = None,
    upsell_amount: float = 0.0,
    discount_percent: float = 0.0,
    retry_count: int = 0,
    already_buyer_approved: bool = False,
) -> PolicyResult:
    """
    Evaluate a proposed checkout total against merchant-configured guardrails.

    Order of checks matters — a BLOCKED result short-circuits immediately,
    since a blocked transaction should never fall through to approval logic.
    """
    checks: list[dict] = []

    def add_check(name: str, passed: bool, detail: str):
        checks.append({"check": name, "passed": passed, "detail": detail})

    # 1. Hard ceiling — no transaction may ever exceed this, approval or not.
    hard_cap = policy.max_transaction_amount
    within_hard_cap = total_amount <= hard_cap
    add_check(
        "max_transaction_amount",
        within_hard_cap,
        f"Total ₹{total_amount:.2f} vs hard cap ₹{hard_cap:.2f}",
    )
    if not within_hard_cap:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=(
                f"Transaction total ₹{total_amount:.2f} exceeds the merchant's maximum "
                f"allowed transaction amount of ₹{hard_cap:.2f}."
            ),
            checks=checks,
        )

    # 2. Buyer-stated budget, if provided by the AI's parsed intent.
    if buyer_budget is not None:
        within_budget = total_amount <= buyer_budget
        add_check(
            "buyer_budget",
            within_budget,
            f"Total ₹{total_amount:.2f} vs buyer budget ₹{buyer_budget:.2f}",
        )
        if not within_budget:
            return PolicyResult(
                decision=PolicyDecision.BLOCKED,
                reason=(
                    f"Transaction total ₹{total_amount:.2f} exceeds the buyer's stated "
                    f"budget of ₹{buyer_budget:.2f}."
                ),
                checks=checks,
            )

    # 3. Upsell ceiling — upsells are capped independently of the base cart.
    upsell_ok = upsell_amount <= policy.max_upsell_amount
    add_check(
        "max_upsell_amount",
        upsell_ok,
        f"Upsell ₹{upsell_amount:.2f} vs limit ₹{policy.max_upsell_amount:.2f}",
    )
    if not upsell_ok:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=(
                f"Suggested upsell of ₹{upsell_amount:.2f} exceeds the configured "
                f"upsell limit of ₹{policy.max_upsell_amount:.2f}."
            ),
            checks=checks,
        )

    # 4. Discount ceiling.
    discount_ok = discount_percent <= policy.max_discount_percent
    add_check(
        "max_discount_percent",
        discount_ok,
        f"Discount {discount_percent:.1f}% vs limit {policy.max_discount_percent:.1f}%",
    )
    if not discount_ok:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=(
                f"Discount of {discount_percent:.1f}% exceeds the allowed maximum "
                f"of {policy.max_discount_percent:.1f}%."
            ),
            checks=checks,
        )

    # 5. Retry ceiling (checked here too so callers can pre-flight before payment).
    retries_ok = retry_count <= policy.max_automatic_retries
    add_check(
        "max_automatic_retries",
        retries_ok,
        f"Retry count {retry_count} vs max {policy.max_automatic_retries}",
    )
    if not retries_ok:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=(
                f"Retry was not attempted because the configured retry limit of "
                f"{policy.max_automatic_retries} has already been reached. No duplicate "
                f"payment was created."
            ),
            checks=checks,
        )

    # 6. Approval threshold — passes all hard limits but still needs a human nod.
    if already_buyer_approved:
        add_check("approval_threshold", True, "Buyer has already approved this transaction.")
        return PolicyResult(
            decision=PolicyDecision.ALLOWED,
            reason="All guardrail checks passed and the buyer has approved this purchase.",
            checks=checks,
        )

    needs_approval = total_amount > policy.approval_threshold
    add_check(
        "approval_threshold",
        not needs_approval,
        f"Total ₹{total_amount:.2f} vs approval threshold ₹{policy.approval_threshold:.2f}",
    )
    if needs_approval:
        return PolicyResult(
            decision=PolicyDecision.REQUIRES_APPROVAL,
            reason=(
                f"This purchase of ₹{total_amount:.2f} exceeds the automatic approval "
                f"threshold of ₹{policy.approval_threshold:.2f} and requires explicit "
                f"buyer confirmation before payment can proceed."
            ),
            checks=checks,
        )

    return PolicyResult(
        decision=PolicyDecision.ALLOWED,
        reason=f"Transaction total ₹{total_amount:.2f} is within all configured guardrails.",
        checks=checks,
    )
