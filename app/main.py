# app/main.py

import time
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.api.auth_routes import auth_router
from app.api.schemas import HealthResponse
from app.db.database import engine, Base
from app.core.logger import logger

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI Career Co-Pilot API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)
app.include_router(auth_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Hər HTTP sorğusunu logla:
    - Method + URL
    - Status code
    - Cavab vaxtı (ms)
    """
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)

    log_msg = (
        f"{request.method} {request.url.path} | "
        f"status={response.status_code} | "
        f"duration={duration_ms}ms"
    )

    if response.status_code >= 500:
        logger.error(log_msg)
    elif response.status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return response


@app.get("/health", response_model=HealthResponse)
async def health():
    logger.info("Health check called")
    return HealthResponse(status="ok", service="ai-career-copilot")


@app.get("/cache/stats")
async def cache_stats():
    from app.core.cache import get_cache_stats

    stats = get_cache_stats()
    logger.info(f"Cache stats: {stats}")
    return stats
