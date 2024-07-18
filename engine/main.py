#!.venv/bin/python
# -*- coding: utf-8 -*-

import sys
# Parse the command line arguments
import argparse
# Asynchronous programming
from concurrent.futures import ThreadPoolExecutor
import asyncio
import nest_asyncio
import signal
# Database
import duckdb
# Pipeline
from crawl import Crawler
from custom_db import index_pages, access_index, save_pages
from download import Downloader, Loader
from summarize import Summarizer
from tokenizer import Tokenizer
from index import Indexer
# Server
from server import start_server

# Threading
MAX_THREADS = 10
ENGINE_NAME = "TüR"

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

# Database setup
con = duckdb.connect("crawlies.db")
with open('setup.sql', 'r') as statements:
    # Execute each statement
    for statement in statements.read().split(';'):
        if statement.strip():  # Skip empty statements
            con.execute(statement)

con.install_extension("fts")
con.load_extension("fts")


async def pipeline(from_crawl: bool = False):
    """
    Start the crawling, tokenizing, and indexing pipeline
    Returns:

    """

    # Initialize the pipeline elements
    crawler = Crawler(con)
    crawler.max_size = 10000
    indexer = Indexer(con)
    tokenizer = Tokenizer(con)
    downloader = Downloader(con)
    loader = Loader(con)
    summarizer = Summarizer(con)

    # Add the pipeline elements
    # Crawler: Crawl the website
    crawler.add_next(downloader)
    crawler.add_next(indexer)
    #crawler.add_next(summarizer)

    # Loader: Load the pages from the disk
    loader.add_next(indexer)
    loader.add_next(summarizer)

    # Indexer: Index the pages
    indexer.add_next(tokenizer)

    def signal_handler(signum, frame):
        print("Interrupt received, shutting down... Please wait. This may take a few seconds.")
        for element in [crawler, indexer, downloader, tokenizer]:
            element.shutdown()

    signal.signal(signal.SIGINT, signal_handler)

    # Initialize the pipeline
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Add the executor to the pipeline elements
        crawler.add_executor(executor)
        indexer.add_executor(executor)
        tokenizer.add_executor(executor)
        downloader.add_executor(executor)
        loader.add_executor(executor)

        # Start the pipeline
        if from_crawl:
            asyncio.run(crawler.process())
        else:
            asyncio.run(loader.process())
        try:
            if from_crawl:
                await crawler.process()
            else:
                await loader.process()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Ensure states are saved even if an exception occurs
            for element in [crawler, indexer, tokenizer]:
                element.save_state()
            index_pages()
            save_pages()
            index_df = access_index()
            index_df.to_csv("inverted_index.csv")
            con.close()
            print("State saved")

    # Compute TF-IDF matrix
    con.execute("""
        WITH 
        DocumentCount(total_docs) AS (
            SELECT COUNT(*) FROM documents
        ),
        TermFrequence AS Inverted_Index,
        DocumentFrequency(word, doc_count) AS (
            SELECT word, COUNT(DISTINCT doc) AS doc_count
            FROM   Inverted_Index
        ),
        TFIDF(doc, word, tfidf) AS (
            SELECT tf.doc, tf.word,
                   tf.amount * LOG((total_docs * 1.0) / df.doc_count)
            FROM   TermFrequency AS tf,
                   DocumentCount AS _(total_docs),
                   DocumentFrequency AS df
            WHERE  tf.word = df.word
        )
        INSERT INTO TFIDFs (doc, word, tfidf)
            SELECT doc, word, tfidf
            FROM   TFIDF
            WHERE  tfidf > 0
    """)

    # Save the state+
    for element in [crawler, indexer, tokenizer]:
        element.save_state()
    index_pages()
    save_pages()
    index_df = access_index()
    index_df.to_csv("inverted_index.csv")
    con.close()
    print("State saved")


def parse_query(filepath) -> list[str]:
    with open(filepath, "r") as file:
        queries = file.readlines()
    return queries


def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description=f"Find anything with {ENGINE_NAME}!")
    parser.add_argument("-q", "--queries", help="Queries file", default="queries.txt", type=str, required=False)
    parser.add_argument("-p", "--pipe", help="Run the pipeline", action="store_true", required=False)
    parser.add_argument("-l", "--load", help="Run pipeline from disk", action="store_true", required=False)
    parser.add_argument("-s", "--server", help="Run the server", action="store_true", required=False)

    try:
        args = parser.parse_args()

        # Start the pipeline
        if args.pipe:
            # Crawl the websites and start the pipeline
            asyncio.run(pipeline(from_crawl=True))
        elif args.load:
            # Load the pages from the disk and start the pipeline
            asyncio.run(pipeline(from_crawl=False))
        elif args.server:
            # Start the server
            start_server()
        else:
            parser.print_help()

    except argparse.ArgumentError as e:
        print(f"An error occurred while parsing the command line arguments: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)
    finally:
        con.close()


if __name__ == "__main__":
    main()
