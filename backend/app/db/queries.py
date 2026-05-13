import asyncpg
from typing import Dict, Any, List

async def insert_paper(conn: asyncpg.Connection, paper: Dict[str, Any]) -> int:
    """
    Insert a paper into the database.
    """
    query = """
    INSERT INTO papers (arxiv_id, title, abstract, authors, arxiv_url, pdf_url, published_date, updated_date, metadata)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    ON CONFLICT (arxiv_id) DO NOTHING
    RETURNING id
    """
    return await conn.fetchval(
        query,
        paper["arxiv_id"],
        paper["title"],
        paper["abstract"],
        paper["authors"],
        paper["arxiv_url"],
        paper["pdf_url"],
        paper["published_date"],
        paper["updated_date"],
        paper.get("metadata"),
    )


async def insert_paper_chunk(conn: asyncpg.Connection, chunk: Dict[str, Any]) -> int:
    """
    Insert a paper chunk into the database.
    """
    query = """
    INSERT INTO paper_chunks (paper_id, chunk_index, content, search_vector)
    VALUES ($1, $2, $3, to_tsvector('english', $3))
    ON CONFLICT (paper_id, chunk_index) DO NOTHING
    RETURNING id
    """
    return await conn.fetchval(
        query,
        chunk["paper_id"],
        chunk["chunk_index"],
        chunk["content"]
    )


async def insert_ingestion_log(conn: asyncpg.Connection, log: Dict[str, Any]) -> int:
    """
    Insert an ingestion log into the database.
    """
    query = """
    INSERT INTO ingestion_logs (arxiv_id, status, error_message)
    VALUES ($1, $2, $3)
    RETURNING id
    """
    return await conn.fetchval(
        query,
        log["arxiv_id"],
        log["status"],
        log["error_message"]
    )


async def search_papers_fts(conn: asyncpg.Connection, query: str, limit: int = 10) -> List[asyncpg.Record]:
    """
    Search papers using full-text search.
    """
    q = """
    WITH ranked_chunks AS (
        SELECT DISTINCT ON (pc.paper_id) 
            pc.paper_id,
            pc.content,
            ts_rank(pc.search_vector, websearch_to_tsquery('english', $1)) as rank
        FROM paper_chunks pc
        WHERE pc.search_vector @@ websearch_to_tsquery('english', $1)
        ORDER BY pc.paper_id, rank DESC
    )
    SELECT
        p.arxiv_id,
        p.title,
        p.abstract,
        p.authors,
        p.pdf_url,
        rc.content as matching_chunk,
        rc.rank
    FROM papers p
    JOIN ranked_chunks rc ON p.id = rc.paper_id
    ORDER BY rc.rank DESC
    LIMIT $2
    """
    return await conn.fetch(q, query, limit)
