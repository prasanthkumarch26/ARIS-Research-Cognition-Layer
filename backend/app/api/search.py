from fastapi import APIRouter, Depends, HTTPException
import asyncio
import asyncpg
from app.db.connection import get_db, get_redis
from app.db.queries import search_papers_fts
from app.services.ingestion_service import IngestionService
from app.services.arxiv_client import ArxivClient
from app.core.config import settings
import redis.asyncio as redis_client

import json

router = APIRouter()

@router.get("/search")
async def search(query: str, conn: asyncpg.Connection = Depends(get_db), limit: int = 10):
    try:
        results = await search_papers_fts(conn, query, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    if results:
        return [dict(row) for row in results]
    else:
        service = IngestionService(ArxivClient())
        await service.ingest_papers(query)
        
        final_results = await search_papers_fts(conn, query, limit)
        if final_results:
            return [dict(row) for row in final_results]
        else:
            raise HTTPException(status_code=404, detail="Error: No results found")


@router.get("/cache/search")
async def search_from_cache(query: str, conn: asyncpg.Connection = Depends(get_db), redis: redis_client.Redis = Depends(get_redis), limit: int = 10):
    try:
        cache_key = f"search:{query.lower().strip()}"
        cached_result = await redis.get(cache_key)

        if cached_result:
            return json.loads(cached_result)
        else:
            results = await asyncio.wait_for(
                search_papers_fts(conn, query, limit),
                timeout=1.0
            )

            if not results:
                service = IngestionService(ArxivClient())
                await service.ingest_papers(query)

                results = await asyncio.wait_for(
                    search_papers_fts(conn, query, limit),
                    timeout=1.0
                )

            if results:
                results_dict = [dict(row) for row in results]
                await redis.set(cache_key, json.dumps(results_dict), ex=settings.redis_ttl_search)
                return results_dict
            else:
                raise HTTPException(status_code=404, detail="Error: No results found")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Error: Database query timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
