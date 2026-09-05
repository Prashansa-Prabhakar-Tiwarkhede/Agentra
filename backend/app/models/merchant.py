from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Merchant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "merchants"

    # Supabase auth user id (owner)
    auth_user_id = Column(String, unique=True, nullable=False, index=True)

    business_name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)

    currency = Column(String, default="INR")
    store_description = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)

    onboarding_complete = Column(Boolean, default=False)

    agent_config = relationship("AgentConfig", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    policy = relationship("Policy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")


class AgentConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_configs"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, unique=True)
    agent_name = Column(String, default="AURA Assistant")
    personality = Column(String, default="friendly, concise, helpful")
    upselling_enabled = Column(Boolean, default=True)
    cross_selling_enabled = Column(Boolean, default=True)
    # comma-separated allowed action names, keeps this simple and explicit
    allowed_actions = Column(String, default="search_products,get_product,compare_products,check_inventory,calculate_cart,create_checkout_intent,request_buyer_approval")

    merchant = relationship("Merchant", back_populates="agent_config")


class Policy(Base, UUIDMixin, TimestampMixin):
    """
    The guardrail configuration. This table is the single source of truth
    the Policy Engine reads from — the LLM never writes to it directly.
    """
    __tablename__ = "policies"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, unique=True)

    max_transaction_amount = Column(Float, default=2000.0)
    approval_threshold = Column(Float, default=1000.0)
    max_automatic_retries = Column(Integer, default=1)
    max_discount_percent = Column(Float, default=10.0)
    max_upsell_amount = Column(Float, default=200.0)

    merchant = relationship("Merchant", back_populates="policy")
