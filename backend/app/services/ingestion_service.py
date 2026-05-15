import asyncio
from app.services.arxiv_client import ArxivClient
from app.db.connection import init_db, close_db, get_db_pool, get_db
from app.db.queries import insert_paper, insert_paper_chunk


class IngestionService:
    def __init__(self, arxiv_client: ArxivClient):
        self.arxiv_client = arxiv_client

    async def ingest_papers(self, query : str, start: int = 0, max_results : int = 20):
        LIMIT = 20
        fetch_count = 0
        all_papers = []
        while fetch_count < max_results:
            curr = min(LIMIT, max_results - fetch_count)
            curr_start = start + fetch_count

            arxiv_papers = await self.arxiv_client.search(query, start=curr_start, max_results=curr)

            if not arxiv_papers:
                break

            fetch_count += len(arxiv_papers)

            papers = []
            for paper in arxiv_papers:
                papers.append({
                    "arxiv_id": paper["arxiv_id"],
                    "title": paper["title"],
                    "abstract": paper["abstract"],
                    "authors": paper["authors"],
                    "arxiv_url": paper["arxiv_url"],
                    "pdf_url": paper["pdf_url"],
                    "published_date": paper["published_date"],
                    "updated_date": paper["updated_date"],
                })
            all_papers.extend(papers)
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                for paper in papers:
                    paper_id = await insert_paper(conn, paper)

                    if not paper_id:
                        paper_id = await conn.fetchval(
                            "SELECT id FROM papers WHERE arxiv_id = $1",
                            paper["arxiv_id"]
                        )

                    if paper_id:
                        chunks = [senstance.strip() for senstance in paper["abstract"].split(".") if senstance.strip()]
                        for i, chunk in enumerate(chunks):
                            await insert_paper_chunk(conn, {
                                "paper_id": paper_id,
                                "chunk_index": i,
                                "content": chunk
                            })
        return all_papers

async def main():
    await init_db()
    ingestion_service = IngestionService(ArxivClient())
    result = await ingestion_service.ingest_papers("transformers", 0, 20)
    print(result)
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
