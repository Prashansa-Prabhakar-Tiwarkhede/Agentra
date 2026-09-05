"""
Seed script for Demo Mode (spec section 28/33).
Creates a demo merchant, 30+ products across 5 categories, sample orders
(successful + failed), agent sessions, and audit events — all clearly
tagged as synthetic so the dashboard can label them as such.

Run: PYTHONPATH=. python3 database/seed.py
"""
import os
import random
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import Base, engine, SessionLocal
from app.models.merchant import Merchant, AgentConfig, Policy
from app.models.product import Product
from app.models.session import AgentSession, AgentMessage
from app.models.order import CheckoutIntent, Order
from app.models.payment import PaymentAttempt
from app.models.audit import AuditEvent
from app.models.base import utcnow

random.seed(42)

CATEGORIES = {
    "Gifts": [
        ("Premium Birthday Gift Box", 1299, ["birthday", "gift", "premium"], {"recipient": "friend", "occasion": "birthday"}),
        ("Anniversary Flower Bouquet", 899, ["anniversary", "flowers", "romantic"], {"occasion": "anniversary"}),
        ("Personalized Photo Frame", 499, ["gift", "personalized"], {"occasion": "any"}),
        ("Luxury Chocolate Hamper", 1099, ["gift", "chocolate", "premium"], {"occasion": "any"}),
        ("Handwritten Card Set", 199, ["gift", "budget"], {"occasion": "any"}),
        ("Scented Candle Trio", 649, ["gift", "home", "relax"], {"occasion": "housewarming"}),
    ],
    "Electronics": [
        ("Wireless Earbuds Pro", 2499, ["electronics", "audio"], {}),
        ("Portable Bluetooth Speaker", 1799, ["electronics", "audio", "gift"], {}),
        ("Smart Fitness Band", 1999, ["electronics", "fitness", "gift"], {}),
        ("Fast Wireless Charger", 899, ["electronics", "accessory"], {}),
        ("USB-C Hub 7-in-1", 1299, ["electronics", "accessory"], {}),
        ("Mechanical Keyboard Mini", 3299, ["electronics", "gaming"], {}),
    ],
    "Fashion": [
        ("Leather Wallet", 799, ["fashion", "accessory", "gift"], {"recipient": "friend"}),
        ("Cotton Graphic T-Shirt", 599, ["fashion", "casual"], {}),
        ("Classic Aviator Sunglasses", 899, ["fashion", "accessory"], {}),
        ("Everyday Tote Bag", 1199, ["fashion", "accessory", "gift"], {"recipient": "friend"}),
        ("Analog Wrist Watch", 2199, ["fashion", "accessory", "gift"], {"occasion": "birthday"}),
        ("Knit Winter Scarf", 499, ["fashion", "winter", "gift"], {"occasion": "any"}),
    ],
    "Home": [
        ("Ceramic Coffee Mug Set", 649, ["home", "kitchen", "gift"], {"occasion": "housewarming"}),
        ("Indoor Plant - Succulent", 349, ["home", "plants", "gift"], {"occasion": "housewarming"}),
        ("Aromatic Diffuser", 899, ["home", "relax"], {}),
        ("Cotton Bedsheet Set", 1599, ["home", "bedroom"], {}),
        ("Table Lamp - Minimalist", 1099, ["home", "decor"], {}),
        ("Woven Storage Basket", 549, ["home", "organizer"], {}),
    ],
    "Books & Stationery": [
        ("Bestseller Novel Bundle", 799, ["books", "gift"], {"recipient": "friend"}),
        ("Leather Journal", 399, ["stationery", "gift"], {"occasion": "any"}),
        ("Premium Pen Set", 599, ["stationery", "gift"], {"occasion": "graduation"}),
        ("Desk Planner 2026", 349, ["stationery", "productivity"], {}),
        ("Sketchbook + Pencil Kit", 449, ["stationery", "art", "gift"], {"recipient": "friend"}),
        ("Motivational Quote Calendar", 299, ["stationery", "gift"], {"occasion": "any"}),
    ],
}

GIFT_WRAP_NAME = "Gift Wrap Add-on"


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(Merchant).filter(Merchant.auth_user_id == "demo-merchant-user").first()
    if existing:
        print("Demo merchant already exists:", existing.id)
        db.close()
        return existing.id

    merchant = Merchant(
        auth_user_id="demo-merchant-user",
        business_name="AURA Demo Store",
        description="Synthetic demo merchant preloaded for hackathon judging.",
        category="General",
        currency="INR",
        store_description="A demo storefront showcasing agentic commerce.",
        contact_email="demo@auracommerce.dev",
        onboarding_complete=True,
    )
    db.add(merchant)
    db.flush()

    db.add(AgentConfig(
        merchant_id=merchant.id,
        agent_name="Aura",
        personality="warm, concise, a little witty",
        upselling_enabled=True,
        cross_selling_enabled=True,
    ))
    db.add(Policy(
        merchant_id=merchant.id,
        max_transaction_amount=5000,
        approval_threshold=1500,
        max_automatic_retries=1,
        max_discount_percent=15,
        max_upsell_amount=300,
    ))
    db.flush()

    # Category-representative placeholder images so the demo actually shows product
    # thumbnails without a merchant needing to add real ones manually.
    CATEGORY_IMAGES = {
        "Gifts": "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=200&h=200&fit=crop",
        "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=200&h=200&fit=crop",
        "Fashion": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=200&h=200&fit=crop",
        "Home": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e6?w=200&h=200&fit=crop",
        "Books & Stationery": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200&h=200&fit=crop",
    }

    products_by_category: dict[str, list[Product]] = {}
    for category, items in CATEGORIES.items():
        products_by_category[category] = []
        for name, price, tags, attrs in items:
            p = Product(
                merchant_id=merchant.id, name=name, description=f"{name} — a great pick for {category.lower()}.",
                category=category, price=price, currency="INR",
                sku=f"{category[:3].upper()}-{random.randint(1000,9999)}",
                inventory=random.randint(5, 60),
                tags=tags, attributes=attrs,
                images=[CATEGORY_IMAGES.get(category)] if category in CATEGORY_IMAGES else [],
            )
            db.add(p)
            products_by_category[category].append(p)
    db.flush()

    # Gift wrap add-on, cross-linked as an upsell target for several Gifts products
    gift_wrap = Product(
        merchant_id=merchant.id, name=GIFT_WRAP_NAME, description="Add festive gift wrapping to any order.",
        category="Add-on", price=149, currency="INR", sku="ADD-0001", inventory=999,
        tags=["gift", "wrap"], attributes={},
    )
    db.add(gift_wrap)
    db.flush()

    for p in products_by_category["Gifts"][:4]:
        p.upsell_product_ids = [gift_wrap.id]
    # cross-sell electronics accessories
    earbuds = next(p for p in products_by_category["Electronics"] if "Earbuds" in p.name)
    charger = next(p for p in products_by_category["Electronics"] if "Charger" in p.name)
    earbuds.cross_sell_product_ids = [charger.id]
    db.commit()

    all_products = [p for plist in products_by_category.values() for p in plist] + [gift_wrap]
    print(f"Seeded {len(all_products)} products across {len(CATEGORIES)} categories + add-ons")

    # --- Sample agent sessions, orders, payments, audit events ---
    now = utcnow()

    def audit(event_type, session_id=None, actor="system", reason=None, policy_decision=None,
               amount=None, result=None, input_data=None, output_data=None, offset_min=0):
        e = AuditEvent(
            merchant_id=merchant.id, session_id=session_id, event_type=event_type, actor=actor,
            reason=reason, policy_decision=policy_decision, amount=amount, result=result,
            input_data=input_data, output_data=output_data,
        )
        e.created_at = now - timedelta(days=random.randint(0, 6), minutes=offset_min)
        db.add(e)
        return e

    # Scenario 1: successful purchase (Premium Gift Box + wrap, ALLOWED)
    gift_box = products_by_category["Gifts"][0]
    s1 = AgentSession(merchant_id=merchant.id, status="completed")
    db.add(s1); db.flush()
    db.add(AgentMessage(session_id=s1.id, role="buyer", content="I need a birthday gift for my friend under ₹1500."))
    db.add(AgentMessage(session_id=s1.id, role="agent", content=f"The {gift_box.name} is a great fit at ₹{gift_box.price:.0f}. Want gift wrapping for ₹149?"))
    audit("AI_SESSION_STARTED", s1.id, offset_min=100)
    audit("PRODUCT_SEARCH", s1.id, reason="Buyer requested birthday gift under ₹1500.", result="success", offset_min=98)
    audit("PRODUCT_RECOMMENDED", s1.id, reason=f"{gift_box.name} matches occasion and budget.", result="success", offset_min=96)
    audit("UPSELL_SUGGESTED", s1.id, reason="Gift wrap add-on offered.", result="success", offset_min=94)
    total1 = gift_box.price + gift_wrap.price
    audit("POLICY_CHECK", s1.id, policy_decision="ALLOWED", amount=total1, result="success",
          reason=f"Transaction total ₹{total1:.0f} is within all configured guardrails.", offset_min=90)
    intent1 = CheckoutIntent(
        merchant_id=merchant.id, session_id=s1.id,
        line_items=[{"product_id": gift_box.id, "name": gift_box.name, "unit_price": gift_box.price, "qty": 1, "line_total": gift_box.price},
                    {"product_id": gift_wrap.id, "name": gift_wrap.name, "unit_price": gift_wrap.price, "qty": 1, "line_total": gift_wrap.price}],
        subtotal=total1, total=total1, currency="INR", idempotency_key=f"seed-intent-{s1.id}",
        policy_decision="ALLOWED", requires_approval=False, buyer_approved=True, status="approved",
    )
    db.add(intent1); db.flush()
    order1 = Order(
        merchant_id=merchant.id, checkout_intent_id=intent1.id, line_items=intent1.line_items,
        amount=total1, currency="INR", payment_status="paid", order_status="completed",
        is_ai_generated=True, razorpay_order_id="order_seed_demo1", razorpay_payment_id="pay_seed_demo1",
    )
    db.add(order1); db.flush()
    audit("ORDER_CREATED", s1.id, amount=total1, result="success", offset_min=89)
    audit("PAYMENT_CREATED", s1.id, amount=total1, result="pending", offset_min=88)
    audit("PAYMENT_SUCCESS", s1.id, amount=total1, result="success", offset_min=86)

    # Scenario 2: payment failure -> retry blocked
    s2 = AgentSession(merchant_id=merchant.id, status="abandoned")
    db.add(s2); db.flush()
    watch = next(p for p in products_by_category["Fashion"] if "Watch" in p.name)
    total2 = watch.price
    audit("AI_SESSION_STARTED", s2.id, offset_min=200)
    audit("PRODUCT_RECOMMENDED", s2.id, reason=f"{watch.name} matches request.", result="success", offset_min=198)
    audit("POLICY_CHECK", s2.id, policy_decision="ALLOWED", amount=total2, result="success", offset_min=196)
    intent2 = CheckoutIntent(
        merchant_id=merchant.id, session_id=s2.id,
        line_items=[{"product_id": watch.id, "name": watch.name, "unit_price": watch.price, "qty": 1, "line_total": watch.price}],
        subtotal=total2, total=total2, currency="INR", idempotency_key=f"seed-intent-{s2.id}",
        policy_decision="ALLOWED", requires_approval=False, buyer_approved=True, status="approved",
    )
    db.add(intent2); db.flush()
    order2 = Order(
        merchant_id=merchant.id, checkout_intent_id=intent2.id, line_items=intent2.line_items,
        amount=total2, currency="INR", payment_status="failed", order_status="cancelled", is_ai_generated=True,
    )
    db.add(order2); db.flush()
    pa1 = PaymentAttempt(order_id=order2.id, checkout_intent_id=intent2.id, idempotency_key=f"{intent2.id}:1",
                          attempt_number=1, amount=total2, currency="INR", status="failed",
                          failure_reason="Card declined by issuing bank (test mode simulation).")
    db.add(pa1)
    audit("PAYMENT_CREATED", s2.id, amount=total2, result="pending", offset_min=194)
    audit("PAYMENT_FAILED", s2.id, reason="Card declined by issuing bank (test mode simulation).", amount=total2, result="failure", offset_min=192)
    audit("RETRY_BLOCKED", s2.id, reason="Retry was not attempted because the configured retry limit of 1 has already been reached. No duplicate payment was created.", amount=total2, result="failure", offset_min=191)

    # Scenario 3: blocked transaction (over hard cap)
    s3 = AgentSession(merchant_id=merchant.id, status="abandoned")
    db.add(s3); db.flush()
    keyboard = next(p for p in products_by_category["Electronics"] if "Keyboard" in p.name)
    audit("AI_SESSION_STARTED", s3.id, offset_min=300)
    audit("PRODUCT_RECOMMENDED", s3.id, reason=f"{keyboard.name} matches request.", result="success", offset_min=298)
    audit("POLICY_CHECK", s3.id, policy_decision="BLOCKED", amount=keyboard.price * 2, result="success",
          reason=f"Transaction total ₹{keyboard.price*2:.0f} exceeds the merchant's maximum allowed transaction amount of ₹5000.00.",
          offset_min=296)

    # Scenario 4: requires approval, then approved and paid
    s4 = AgentSession(merchant_id=merchant.id, status="completed")
    db.add(s4); db.flush()
    hamper = products_by_category["Gifts"][3]
    earbuds_p = earbuds
    total4 = hamper.price + earbuds_p.price
    audit("AI_SESSION_STARTED", s4.id, offset_min=400)
    audit("POLICY_CHECK", s4.id, policy_decision="REQUIRES_APPROVAL", amount=total4, result="success",
          reason=f"This purchase of ₹{total4:.0f} exceeds the automatic approval threshold of ₹1500.00.", offset_min=396)
    audit("BUYER_APPROVAL_REQUESTED", s4.id, amount=total4, result="pending", offset_min=395)
    audit("BUYER_APPROVED", s4.id, actor="buyer", amount=total4, policy_decision="ALLOWED", result="success", offset_min=390)
    intent4 = CheckoutIntent(
        merchant_id=merchant.id, session_id=s4.id,
        line_items=[{"product_id": hamper.id, "name": hamper.name, "unit_price": hamper.price, "qty": 1, "line_total": hamper.price},
                    {"product_id": earbuds_p.id, "name": earbuds_p.name, "unit_price": earbuds_p.price, "qty": 1, "line_total": earbuds_p.price}],
        subtotal=total4, total=total4, currency="INR", idempotency_key=f"seed-intent-{s4.id}",
        policy_decision="ALLOWED", requires_approval=True, buyer_approved=True, status="approved",
    )
    db.add(intent4); db.flush()
    order4 = Order(
        merchant_id=merchant.id, checkout_intent_id=intent4.id, line_items=intent4.line_items,
        amount=total4, currency="INR", payment_status="paid", order_status="completed", is_ai_generated=True,
        razorpay_order_id="order_seed_demo4", razorpay_payment_id="pay_seed_demo4",
    )
    db.add(order4)
    audit("ORDER_CREATED", s4.id, amount=total4, result="success", offset_min=389)
    audit("PAYMENT_SUCCESS", s4.id, amount=total4, result="success", offset_min=385)

    db.commit()
    print("Seeded 4 demo scenarios: success / payment-failure-retry-blocked / blocked / approval-required.")
    print("Demo merchant id:", merchant.id)
    db.close()
    return merchant.id


if __name__ == "__main__":
    seed()
