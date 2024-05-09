CREATE TABLE visited_wikis(
    doc_id integer PRIMARY KEY,
    title VARCHAR(250)
);

CREATE TABLE wiki_summaries(
    doc_id integer PRIMARY KEY,
    summary VARCHAR(200),
    FOREIGN KEY (doc_id) REFERENCES visited_wikis (doc_id)
)