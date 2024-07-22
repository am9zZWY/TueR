#!.venv/bin/python
# -*- coding: utf-8 -*-
import os
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
from download import Downloader, Loader
from tokenizer import Tokenizer
from index import Indexer

# Server
from server import start_server

# Rank
from rank import rank_from_file

# Threading
MAX_THREADS = 10
ENGINE_NAME = "TüR"

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

# Database setup
con = duckdb.connect("crawlies.db")
if not os.path.isfile("crawler_states/global.json"):
    with open("setup.sql", "r") as statements:
        # Execute each statement
        for statement in statements.read().split(";"):
            if statement.strip():  # Skip empty statements
                con.execute(statement)

        con.install_extension("fts")
        con.load_extension("fts")

# Shutdown event for the pipeline
shutdown_event = asyncio.Event()
is_shutting_down = False


async def shutdown_pipeline(stages):
    print("Initiating pipeline shutdown...")
    shutdown_tasks = [stage.shutdown() for stage in stages]
    await asyncio.gather(*shutdown_tasks)
    print("Pipeline shutdown complete.")


async def pipeline(online: bool = True):
    """
    Start the crawling, tokenizing, and indexing pipeline
    Returns: None

    """

    # Initialize the pipeline elements
    crawler = Crawler(con)
    crawler.max_size = 10000
    crawler.max_retries = 1
    crawler.max_concurrent = 5
    indexer = Indexer(con)
    tokenizer = Tokenizer(con)
    downloader = Downloader(con)
    loader = Loader(con)

    # Define the pipeline stages
    stages = [crawler, indexer, tokenizer, downloader, loader]

    # Configure the pipeline structure
    crawler.add_next(downloader)
    crawler.add_next(indexer)

    loader.add_next(indexer)

    indexer.add_next(tokenizer)

    def signal_handler(signum, frame):
        print(
            "Interrupt received, shutting down... Please wait. This may take a few seconds."
        )
        global is_shutting_down
        if not is_shutting_down:
            is_shutting_down = True
            asyncio.get_running_loop().call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize the pipeline
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Add the executor to the pipeline elements
        for stage in stages:
            stage.add_executor(executor)

        # Start the pipeline
        start_element = crawler if online else loader
        process_task = asyncio.create_task(start_element.process())

        try:
            # Wait for the shutdown event
            await shutdown_event.wait()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Shutdown all elements
            await shutdown_pipeline(stages)

    # Compute TF-IDF matrix
    con.execute("TRUNCATE IDFs")
    con.execute(
        """
        INSERT INTO IDFs(word, idf)
        SELECT word, LOG(N::double / COUNT(DISTINCT doc))
        FROM   TFs, (SELECT COUNT(*) FROM documents) AS _(N)
        GROUP BY word, N
    """
    )
    con.close()


def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description=f"Find anything with {ENGINE_NAME}!")
    parser.add_argument(
        "--online",
        help="Run pipeline from the web (online)",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--offline",
        help="Run pipeline from the disk (offline)",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-s", "--server", help="Run the server", action="store_true", required=False
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Queries file",
        default="queries.txt",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-d", "--debug", help="Debug mode", action="store_true", required=False
    )

    try:
        args = parser.parse_args()

        # Start the pipeline
        if args.online:
            # Crawl the websites and start the pipeline
            asyncio.run(pipeline(online=True))
        elif args.offline:
            # Load the pages from the disk and start the pipeline
            asyncio.run(pipeline(online=False))
        elif args.server:
            # Start the server
            start_server(debug=args.debug, con=con)
        elif args.file:
            # Rank the queries from the file
            rank_from_file(args.file)
        else:
            parser.print_help()

    except argparse.ArgumentError as e:
        print(
            f"An error occurred while parsing the command line arguments: {str(e)}",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)
    finally:
        con.close()


if __name__ == "__main__":
    main()
