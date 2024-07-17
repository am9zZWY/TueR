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
from tokenizer import Tokenizer
from index import Indexer

# Threading
MAX_THREADS = 10
ENGINE_NAME = "TüR"

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

# Database setup
con = duckdb.connect("crawlies.db")
con.install_extension("fts")
con.load_extension("fts")


async def crawl():
    """
    Start the crawling, tokenizing, and indexing pipeline
    Returns:

    """

    # Initialize the pipeline elements
    crawler = Crawler(con)
    crawler.max_size = 1000
    indexer = Indexer()
    tokenizer = Tokenizer()

    # Add the pipeline elements
    crawler.add_next(indexer)
    indexer.add_next(tokenizer)

    def signal_handler(signum, frame):
        print("Interrupt received, shutting down... Please wait. This may take a few seconds.")
        for element in [crawler, indexer, tokenizer]:
            element.shutdown()

    signal.signal(signal.SIGINT, signal_handler)

    # Initialize the pipeline
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Add the executor to the pipeline elements
        crawler.add_executor(executor)
        indexer.add_executor(executor)
        tokenizer.add_executor(executor)

        # Start the pipeline
        asyncio.run(crawler.process())
        try:
            await crawler.process()
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
    try:
        # Parse the command line arguments
        parser = argparse.ArgumentParser(description=f"Find anything with {ENGINE_NAME}!")
        parser.add_argument("-q", "--queries", help="Queries file", default="queries.txt", type=str, required=False)
        parser.add_argument("-c", "--crawl", help="Crawl the website", action="store_true", required=False)
        parser.add_argument("-s", "--server", help="Run the server", action="store_true", required=False)

        args = parser.parse_args()

        # Start the pipeline
        if args.crawl:
            asyncio.run(crawl())
        elif args.server:
            print("Starting the server...")
        else:
            parser.print_help()

    except argparse.ArgumentError as e:
        print(f"An error occurred while parsing the command line arguments: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    main()
