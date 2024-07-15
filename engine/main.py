#!.venv/bin/python

"""
Pipeline for Crawling, Tokenizing, and Indexing
"""
import signal
from concurrent.futures import ThreadPoolExecutor
import asyncio
import nest_asyncio

# Database
import duckdb
# Pipeline
from crawl import Crawler
from custom_db import index_pages, access_index, save_pages
from custom_tokenizer import Tokenizer
from index import Indexer

# Constants
MAX_THREADS = 10

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

# Database setup
con = duckdb.connect("crawlies.db")
con.install_extension("fts")
con.load_extension("fts")

# Initialize the pipeline elements
crawler = Crawler(con)
crawler.max_size = 1000
indexer = Indexer()
tokenizer = Tokenizer()

# Add the pipeline elements
crawler.add_next(indexer)
indexer.add_next(tokenizer)


def signal_handler(signum, frame):
    print("Interrupt received, shutting down... Please wait")
    for element in [crawler, indexer, tokenizer]:
        element.shutdown()


signal.signal(signal.SIGINT, signal_handler)


async def main():
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


if __name__ == "__main__":
    asyncio.run(main())
