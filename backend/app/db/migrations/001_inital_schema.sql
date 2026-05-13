CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- PAPERS TABLE
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxiv_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    authors TEXT[],
    arxiv_url TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    published_date TEXT,
    updated_date TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PAPER CHUNKS TABLE
CREATE TABLE IF NOT EXISTS paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    search_vector TSVECTOR,
    
    -- Prevent duplicate chunk ordering per paper
    UNIQUE (paper_id, chunk_index)
);

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_paper_chunks_search_vector
ON paper_chunks USING GIN (search_vector);

-- index for faster joins
CREATE INDEX IF NOT EXISTS idx_paper_chunks_paper_id
ON paper_chunks (paper_id);

-- INGESTION LOGS TABLE
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxiv_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- index for querying logs by arxiv_id
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_arxiv_id
ON ingestion_logs (arxiv_id);
