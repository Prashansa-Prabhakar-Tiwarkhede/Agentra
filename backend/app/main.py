from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import Base, engine
from app import models  # noqa: F401 — ensures all models are registered before create_all
from app.rate_limit import limiter
from app.api import merchants, products, agent, checkout, payments, orders, audit, analytics

settings = get_settings()

app = FastAPI(
    title="AURA Commerce API",
    description="Commerce built for the age of AI buyers.",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev convenience: auto-create tables against a local/sqlite DB.
    # Production (Supabase Postgres) should use Alembic migrations instead.
    Base.metadata.create_all(bind=engine)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak raw stack traces to the client (spec section 35).
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
    )


@app.get("/")
def root():
    return {"service": "AURA Commerce API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy", "razorpay_configured": settings.is_razorpay_configured}


app.include_router(merchants.router)
app.include_router(products.router)
app.include_router(agent.router)
app.include_router(checkout.router)
app.include_router(payments.router)
app.include_router(orders.router)
app.include_router(audit.router)
app.include_router(analytics.router)
