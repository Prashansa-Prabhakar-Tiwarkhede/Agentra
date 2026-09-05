from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_auth_user_id, get_current_merchant
from app.database import get_db
from app.models.merchant import Merchant, AgentConfig, Policy
from app.schemas.merchant import (
    MerchantCreate, MerchantOut, AgentConfigUpdate, AgentConfigOut, PolicyUpdate, PolicyOut,
)

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("", response_model=MerchantOut)
def create_merchant(
    payload: MerchantCreate,
    auth_user_id: str = Depends(get_current_auth_user_id),
    db: Session = Depends(get_db),
):
    existing = db.query(Merchant).filter(Merchant.auth_user_id == auth_user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Merchant profile already exists for this account")

    merchant = Merchant(auth_user_id=auth_user_id, **payload.model_dump())
    db.add(merchant)
    db.flush()

    db.add(AgentConfig(merchant_id=merchant.id))
    db.add(Policy(merchant_id=merchant.id))
    db.commit()
    db.refresh(merchant)
    return merchant


@router.get("/me", response_model=MerchantOut)
def get_me(merchant: Merchant = Depends(get_current_merchant)):
    return merchant


@router.put("/me/complete-onboarding", response_model=MerchantOut)
def complete_onboarding(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    merchant.onboarding_complete = True
    db.commit()
    db.refresh(merchant)
    return merchant


@router.get("/me/agent-config", response_model=AgentConfigOut)
def get_agent_config(merchant: Merchant = Depends(get_current_merchant)):
    return merchant.agent_config


@router.put("/me/agent-config", response_model=AgentConfigOut)
def update_agent_config(
    payload: AgentConfigUpdate,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    cfg = merchant.agent_config
    data = payload.model_dump(exclude_unset=True)
    if "allowed_actions" in data and data["allowed_actions"] is not None:
        data["allowed_actions"] = ",".join(data["allowed_actions"])
    for k, v in data.items():
        setattr(cfg, k, v)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.get("/me/policy", response_model=PolicyOut)
def get_policy(merchant: Merchant = Depends(get_current_merchant)):
    return merchant.policy


@router.put("/me/policy", response_model=PolicyOut)
def update_policy(
    payload: PolicyUpdate,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    policy = merchant.policy
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)
    db.commit()
    db.refresh(policy)
    return policy
