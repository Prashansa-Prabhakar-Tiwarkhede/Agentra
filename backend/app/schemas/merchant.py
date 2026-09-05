from pydantic import BaseModel, Field


class MerchantCreate(BaseModel):
    business_name: str
    logo_url: str | None = None
    description: str | None = None
    category: str | None = None
    currency: str = "INR"
    store_description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class MerchantOut(BaseModel):
    id: str
    business_name: str
    logo_url: str | None
    description: str | None
    category: str | None
    currency: str
    store_description: str | None
    contact_email: str | None
    contact_phone: str | None
    onboarding_complete: bool

    class Config:
        from_attributes = True


class AgentConfigUpdate(BaseModel):
    agent_name: str | None = None
    personality: str | None = None
    upselling_enabled: bool | None = None
    cross_selling_enabled: bool | None = None
    allowed_actions: list[str] | None = None


class AgentConfigOut(BaseModel):
    agent_name: str
    personality: str
    upselling_enabled: bool
    cross_selling_enabled: bool
    allowed_actions: str

    class Config:
        from_attributes = True


class PolicyUpdate(BaseModel):
    max_transaction_amount: float | None = Field(default=None, gt=0)
    approval_threshold: float | None = Field(default=None, gt=0)
    max_automatic_retries: int | None = Field(default=None, ge=0)
    max_discount_percent: float | None = Field(default=None, ge=0, le=100)
    max_upsell_amount: float | None = Field(default=None, ge=0)


class PolicyOut(BaseModel):
    max_transaction_amount: float
    approval_threshold: float
    max_automatic_retries: int
    max_discount_percent: float
    max_upsell_amount: float

    class Config:
        from_attributes = True
