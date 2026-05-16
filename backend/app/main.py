from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import asyncpg

from app.db.connection import init_db, close_db, get_db, init_redis, close_redis
from app.api.search import router as search_router
from app.core.middleware import load_shedding_middleware
from starlette.middleware.base import BaseHTTPMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("System starting up...")
    await init_db()
    await init_redis()
    yield
    print("System shutting down...")
    await close_db()
    await close_redis()


app = FastAPI(
    title="ARIS Cognition Layer",
    description="Scalable document ingestion, search, and ranking backend",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(search_router)
app.add_middleware(BaseHTTPMiddleware, dispatch=load_shedding_middleware)


@app.get("/health")
async def health_check(conn: asyncpg.Connection = Depends(get_db)):
    try:
        result = await conn.fetchval("SELECT 1")
        if result == 1:
            return {
                "status": "ok",
                "service": "paper-intelligence-backend",
                "db": "connected"
            }
        return {
            "status": "error",
            "service": "paper-intelligence-backend",
            "db": "unexpected response"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "paper-intelligence-backend",
            "db": "disconnected",
            "error": str(e)
        }
