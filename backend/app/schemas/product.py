from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    price: float = Field(gt=0)
    currency: str = "INR"
    sku: str | None = None
    inventory: int = Field(default=0, ge=0)
    images: list[str] = []
    tags: list[str] = []
    attributes: dict = {}
    upsell_product_ids: list[str] = []
    cross_sell_product_ids: list[str] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    sku: str | None = None
    inventory: int | None = Field(default=None, ge=0)
    images: list[str] | None = None
    tags: list[str] | None = None
    attributes: dict | None = None
    upsell_product_ids: list[str] | None = None
    cross_sell_product_ids: list[str] | None = None


class ProductOut(BaseModel):
    id: str
    merchant_id: str
    name: str
    description: str | None
    category: str | None
    price: float
    currency: str
    sku: str | None
    inventory: int
    images: list
    tags: list
    attributes: dict
    upsell_product_ids: list
    cross_sell_product_ids: list

    class Config:
        from_attributes = True
