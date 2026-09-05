from sqlalchemy import Column, Float, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)

    price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    sku = Column(String, nullable=True)
    inventory = Column(Integer, default=0)

    images = Column(JSON, default=list)     # list[str]
    tags = Column(JSON, default=list)       # list[str] e.g. ["birthday","gift","premium"]
    attributes = Column(JSON, default=dict) # dict e.g. {"recipient":"friend","occasion":"birthday"}

    upsell_product_ids = Column(JSON, default=list)     # list[str]
    cross_sell_product_ids = Column(JSON, default=list) # list[str]

    merchant = relationship("Merchant", back_populates="products")

    def to_ai_context(self) -> dict:
        """
        The ONLY representation the LLM ever sees for a product.
        Deliberately excludes internal ids beyond what's needed to reference it,
        merchant internals, and anything not relevant to buyer decisions.
        """
        return {
            "product_id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "currency": self.currency,
            "in_stock": self.inventory > 0,
            "tags": self.tags or [],
            "attributes": self.attributes or {},
            "image_url": (self.images or [None])[0],
        }
