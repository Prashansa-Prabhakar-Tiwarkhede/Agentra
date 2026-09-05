from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class AgentSession(Base, UUIDMixin, TimestampMixin):
    """One conversation between a buyer (human or AI-driven) and a merchant's agent."""
    __tablename__ = "agent_sessions"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    buyer_ref = Column(String, nullable=True)  # anonymous/session-scoped buyer identifier
    status = Column(String, default="active")  # active, completed, abandoned

    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")


class AgentMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_messages"

    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # buyer | agent | system
    content = Column(String, nullable=False)
    # structured action the agent proposed in this turn, if any (never executed directly from here)
    structured_action = Column(JSON, nullable=True)

    session = relationship("AgentSession", back_populates="messages")
