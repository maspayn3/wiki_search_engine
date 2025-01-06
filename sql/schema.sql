CREATE TABLE documents(
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT,
    summary VARCHAR(250)
);

-- Create index for title searches and URL lookups
CREATE INDEX idx_documents_title ON documents(title);
CREATE INDEX idx_documents_url ON documents(url);
CREATE UNIQUE INDEX idx_documents_url_unique ON documents(url);

CREATE TABLE document_content(
    doc_id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
)