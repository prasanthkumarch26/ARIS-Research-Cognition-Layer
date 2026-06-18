

CREATE TABLE IF NOT EXISTS paper_processing_status {
    paper_id UUID PRIMARY KEY REFERENCES papers(id),
    parse_status VARCHAR(20) DEFAULT 'pending',
    embedding_status VARCHAR(20) DEFAULT 'pending',
    summary_status VARCHAR(20) DEFAULT 'pending',
    chat_ready BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
};


