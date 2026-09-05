"""
Shared Limiter instance. Lives in its own module so both app/main.py (which registers it
with the FastAPI app) and individual route modules (which apply @limiter.limit(...) decorators)
can import it without creating a circular import between main.py and app/api/*.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
