from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import asyncio
import asyncpg
from app.db.connection import get_db, get_redis, get_db_pool
from app.db.queries import search_papers_fts
from app.services.ingestion_service import IngestionService
from app.services.arxiv_client import ArxivClient
from app.core.config import settings
import redis.asyncio as redis_client

import json

router = APIRouter()
service = IngestionService(ArxivClient())

@router.get("/search")
async def search(query: str, limit: int = 10):
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            results = await search_papers_fts(conn, query, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    if results:
        return [dict(row) for row in results]
    else:
        service = IngestionService(ArxivClient())
        await service.ingest_papers(query)
        
        async with pool.acquire() as conn:
            final_results = await search_papers_fts(conn, query, limit)
            if final_results:
                return [dict(row) for row in final_results]
            else:
                raise HTTPException(status_code=404, detail="Error: No results found")


@router.get("/cache/search")
async def search_from_cache(background_tasks: BackgroundTasks,query: str, papers: int = None, limit: int = 10, redis: redis_client.Redis = Depends(get_redis)):
    default_limit = 20

    try:
        pool = await get_db_pool()
        cache_key = f"search:{query.lower().strip()}"
        cached_result = await redis.get(cache_key)

        if papers is not None and papers > default_limit:
            is_ingesting = await redis.get(f"ingesting:{query}")
            if not is_ingesting:
                await redis.set(f"ingesting:{query}", "1", ex=settings.redis_ttl_search)
                remaining_to_fetch = papers - default_limit

                background_tasks.add_task(
                    service.ingest_papers,
                    query,
                    start=default_limit,
                    max_results=remaining_to_fetch
                )

        if cached_result:
            return json.loads(cached_result)
        else:
            async with pool.acquire() as conn:
                results = await asyncio.wait_for(
                    search_papers_fts(conn, query, limit),
                    timeout=5.0
                )

            if len(results) < limit:
                await service.ingest_papers(query, max_results=default_limit)

                async with pool.acquire() as conn:
                    results = await asyncio.wait_for(
                        search_papers_fts(conn, query, limit),
                        timeout=5.0
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
