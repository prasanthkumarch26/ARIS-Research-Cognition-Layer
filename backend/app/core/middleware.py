from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings


MAX_CONCURRENT_REQUESTS = settings.max_concurrent_requests
active_requests = 0

async def load_shedding_middleware(request: Request, call_next):
    global active_requests

    if active_requests >= MAX_CONCURRENT_REQUESTS:
        return JSONResponse(
            status_code=503,
            content={"detail": "Error: Service overloaded. Please try again later."}
        )

    active_requests += 1

    try:
        response = await call_next(request)
        return response
    finally:
        active_requests -= 1
