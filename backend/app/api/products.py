from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_merchant
from app.database import get_db
from app.models.merchant import Merchant
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    category: str | None = None,
    q: str | None = Query(default=None, description="search text"),
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.merchant_id == merchant.id)
    if category:
        query = query.filter(Product.category == category)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    return query.order_by(Product.created_at.desc()).all()


@router.post("", response_model=ProductOut)
def create_product(payload: ProductCreate, merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    product = Product(merchant_id=merchant.id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str, merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.merchant_id == merchant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: str, payload: ProductUpdate, merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.merchant_id == merchant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: str, merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.merchant_id == merchant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"deleted": True, "product_id": product_id}
