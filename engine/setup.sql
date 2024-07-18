-- Setup index database 'crawlies.db'

-- DROP EVERYTHING
DROP TABLE IF EXISTS crawled;
DROP TABLE IF EXISTS TFIDFs;
DROP TABLE IF EXISTS Inverted_Index;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS words;

DROP SEQUENCE IF EXISTS doc_ids;
DROP SEQUENCE IF EXISTS word_ids;

CREATE SEQUENCE doc_ids START 1;
CREATE SEQUENCE word_ids START 1;

CREATE TABLE crawled (
    id      INTEGER DEFAULT nextval('doc_ids') PRIMARY KEY,
    link    VARCHAR UNIQUE NOT NULL,
    html    VARCHAR NOT NULL
);

CREATE TABLE documents (
    id          INTEGER DEFAULT nextval('doc_ids') PRIMARY KEY,
    link        VARCHAR NOT NULL,
    title       VARCHAR,
    description VARCHAR,
    summary     VARCHAR DEFAULT 'no summary'
);

CREATE TABLE words (
    word VARCHAR DEFAULT nextval('word_ids') PRIMARY KEY,
    id   INTEGER DEFAULT nextval('word_ids') UNIQUE
);

CREATE TABLE Inverted_Index (
    word INTEGER,
    doc  INTEGER,
    amount INTEGER,
    PRIMARY KEY (word, doc),
    FOREIGN KEY (word) ON words(id),
    FOREIGN KEY (doc)  ON documents(id)
);

CREATE INDEX inverted_index_word(word);

CREATE TABLE TFIDFs (
    doc   INTEGER,
    word  INTEGER,
    tfidf NUMERIC(10,9) NOT NULL,
    PRIMARY KEY (word, doc),
    FOREIGN KEY (word) ON words(id),
    FOREIGN KEY (doc) ON documents(id)
);

CREATE INDEX tfidfs_word(word);
