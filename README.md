# A.X.I.O.M. – Paper Intelligence System

A production-grade asynchronous full-text search and ingestion system for scientific papers (arXiv).  
Built using a **read-through cache architecture with PostgreSQL GIN-based full-text search**, enabling real-time scientific paper retrieval, indexing, and ranking.

---

## ⚡ System Performance (Load Tested)

### Peak Load: 600 users @ 25 users/sec

- **Throughput:** ~295 RPS (1M+ requests/hour equivalent)
- **Latency:** P95 ~58ms, P99 ~130ms
- **Error Rate:** ~0% (13–46 transient failures over 1M+ requests)
- **Cache Performance:**
  - `/cache/search`: P95 ~56ms
  - `/search`: P95 ~63ms

### Stability Under Load

- Sustained performance under **500–600 concurrent users**
- No cascading failures under 30-minute stress tests
- Controlled degradation under peak load via cached query reuse
- Stable throughput under sustained high-concurrency traffic

---

## 🧠 System Architecture

A **read-through cache + on-demand ingestion pipeline**:

1. User query hits FastAPI backend
2. System first checks **PostgreSQL GIN full-text search index**
3. On cache miss:
   - Async fetch from arXiv API
   - XML parsing and abstract chunking
   - Conversion into PostgreSQL `tsvector`
   - Indexed in real time for future queries
4. Ranked results returned using PostgreSQL `ts_rank`

This design ensures repeated queries are served directly from indexed storage, minimizing external API dependency.

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

### Read-Through Cache Design
- Cache layer backed by pre-indexed PostgreSQL results
- Avoids repeated ingestion for previously queried topics
- Ensures low-latency repeated query execution

### High-Concurrency Data Layer
- `asyncpg` connection pooling for high throughput
- Lock-coordinated ingestion to prevent duplicate writes
- Safe concurrent query + ingestion handling

### Frontend Optimization
- Next.js 15 App Router with React Server Components (RSC)
- Server-side data fetching eliminates CORS overhead
- Optimized UI rendering for fast search response display

---

## 🧪 Load Test Summary

| Metric | Value |
|--------|------|
| Max RPS | ~295 |
| Total Requests | 1M+ |
| P95 Latency | ~58ms |
| P99 Latency | ~130ms |
| Failure Rate | ~0% |
| Concurrent Users | 500–600 |

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
![Desktop View](public/desktop-view.png)

### Mobile View
![Mobile View](public/mobile-view.png)

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
axiomresearch.vercel.app

---

## 🔭 Future Improvements

- Redis caching layer for sub-10ms response optimization
- Background queue system (Celery/RQ) for ingestion decoupling
- LLM-based summarization of retrieved papers (Ollama integration)
- Horizontal scaling with stateless API replicas
