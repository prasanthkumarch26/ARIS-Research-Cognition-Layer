# A.R.I.S. - Adaptive Research Intelligence System

A production-grade asynchronous full-text search and ingestion system for scientific papers (arXiv).  
Built using a **read-through cache architecture with PostgreSQL GIN-based full-text search**, enabling real-time scientific paper retrieval, indexing, and ranking.

---

## ⚡ System Performance (Load Tested)

### Peak Load: 600 users @ 25 users/sec

- **Throughput:** ~294 RPS (Over 1,059,000 requests processed)
- **Latency:** P50 ~11ms, P95 ~64ms
- **Error Rate:** ~0.83% (Graceful 503 load shedding, 0% DB crashes)
- **Cache Performance:**
  - `/cache/search`: P50 ~10ms, P95 ~64ms

### Stability Under Load

- Sustained performance under **500–600 concurrent users**
- No cascading failures under 1hr stress tests
- Controlled degradation under peak load via cached query reuse
- Stable throughput under sustained high-concurrency traffic

---

## 🧠 System Architecture

A **distributed read-through cache + background hydration pipeline**:

1. User query hits FastAPI backend.
2. System first checks **Redis** for sub-millisecond cached JSON results.
3. On Redis miss, system checks **PostgreSQL GIN full-text search index**.
4. On DB miss (or insufficient papers):
   - **Immediate Hydration:** Synchronously fetches the first 20 papers from arXiv to ensure instant UI rendering.
   - **Background Hydration:** Hands the remaining requested papers to a FastAPI `BackgroundTask` for silent ingestion.
   - **Stampede Protection:** Uses a Redis distributed lock (`ingesting:{query}`) to ensure 600 concurrent users don't trigger duplicate background tasks.
5. Ranked results returned using PostgreSQL `ts_rank` and cached in Redis.

---

## 🚀 Key Features

### Asynchronous Ingestion Pipeline
- Built with `httpx` for non-blocking HTTP requests
- Async XML parsing for arXiv Atom feeds
- Efficient chunking of scientific abstracts for indexing

### Full-Text Search Engine (PostgreSQL GIN)
- Sentence-level abstract decomposition
- PostgreSQL native `to_tsvector` indexing
- Ranked retrieval using `ts_rank`
- Deduplication using `DISTINCT ON`
- Sub-100ms query performance for cached data

### Distributed Caching & Stampede Protection
- Redis caching layer for sub-10ms response optimization
- Distributed locking (`ingesting:{query}`) prevents Cache Stampedes (Thundering Herd problem)
- Avoids repeated ingestion for previously queried topics

### Asynchronous Background Hydration
- Hybrid sync/async fetching (first 20 papers sync, remaining async)
- FastAPI `BackgroundTasks` for non-blocking data ingestion
- `asyncio.Lock` rate-limiting to comply with arXiv API limits without blocking the event loop

### High-Concurrency Data & Resilience Layer
- `asyncpg` connection pooling with strict lifecycle management (manual acquire/release to prevent starvation)
- **Load Shedding Middleware:** Automatically rejects excess traffic (503s) to protect database integrity under extreme load
- Singleton `httpx.AsyncClient` preventing TCP socket exhaustion under 600+ concurrent connections

### Frontend Optimization
- Next.js 15 App Router with React Server Components (RSC)
- Server-side data fetching eliminates CORS overhead
- Optimized UI rendering for fast search response display

---

## 🧪 Load Test Summary

| Metric | Value |
|--------|------|
| Max RPS | ~294 |
| Total Requests | 1,059,407 |
| Median Latency (P50) | ~11ms |
| P95 Latency | ~64ms |
| Failure Rate | ~0.83% (Load Shedded) |
| Concurrent Users | 600 |

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python, asyncpg
- **Database:** PostgreSQL (GIN, Full-Text Search, tsvector)
- **Frontend:** Next.js 15, TypeScript, TailwindCSS
- **Infrastructure:** Docker Compose

---

## 🧩 System Design Highlights

- Read-through caching to eliminate repeated external API calls
- PostgreSQL-native full-text search instead of external search engines
- Lock-coordinated ingestion pipeline preventing race conditions under concurrency
- Async architecture optimized for high RPS workloads
- Strong focus on P99 latency control under load testing

---

## 📸 Interface Preview

### Desktop View
![Desktop View](assests/desktop-view.png)

### Mobile View
![Mobile View](assests/mobile-view.png)

---

## ⚙️ How to Run Locally

### 1. Start Database
```bash
docker-compose up -d
```

### 2. Run Backend
```bash
cd backend
python app/migrations.py
uvicorn app.main:app --reload
```

Backend runs at:
http://127.0.0.1:8000

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:
aris.vercel.app

---

## 🔭 Future Improvements

- Phase 2: PDF Parsing & Text Extraction Pipeline (PyMuPDF)
- LLM-based summarization and methodology extraction of retrieved papers (Ollama / Qwen integration)
- Vector Embeddings for semantic search
- Horizontal scaling with stateless API replicas
