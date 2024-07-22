-- Setup index database 'crawlies.db'

-- DROP EVERYTHING
DROP TABLE IF EXISTS crawled;
DROP TABLE IF EXISTS IDFs;
DROP TABLE IF EXISTS TFs;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS words;

DROP SEQUENCE IF EXISTS doc_ids;
DROP SEQUENCE IF EXISTS word_ids;

CREATE SEQUENCE doc_ids START 1;
CREATE SEQUENCE word_ids START 1;

CREATE TABLE crawled (
    link    VARCHAR PRIMARY KEY,
    content BLOB NOT NULL
);

CREATE TABLE documents (
    id          INTEGER DEFAULT nextval('doc_ids') PRIMARY KEY,
    link        VARCHAR NOT NULL,
    title       VARCHAR,
    description VARCHAR,
    summary     VARCHAR DEFAULT 'no summary'
);

CREATE TABLE words (
    word        VARCHAR PRIMARY KEY,
    id          INTEGER DEFAULT nextval('word_ids') UNIQUE,
);

CREATE TABLE TFs (
    word INTEGER,
    doc  INTEGER,
    tf   INTEGER,
    PRIMARY KEY (word, doc),
    FOREIGN KEY (word) REFERENCES words (id),
    FOREIGN KEY (doc)  REFERENCES documents (id)
);

CREATE TABLE IDFs (
    word INTEGER PRIMARY KEY,
    idf  DOUBLE NOT NULL,
    FOREIGN KEY (word) REFERENCES words (id)
)
