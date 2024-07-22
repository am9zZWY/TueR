import lzma
import pickle

import duckdb
from bs4 import BeautifulSoup

from pipeline import PipelineElement


class Downloader(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Downloader")
        self.cursor = dbcon.cursor()

    def __del__(self):
        self.cursor.close()

    async def process(self, data, link):
        """
        Writes the BeautifulSoup object to a file if it's not None.
        """
        if data is None or not isinstance(data, BeautifulSoup):
            print(f"Failed to process {link}. Invalid or empty data.")
            return

        self.cursor.execute(
            """INSERT INTO crawled(link, content) VALUES (?, ?)""",
            [link, lzma.compress(pickle.dumps(data))],
        )


class Loader(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Loader")
        self.cursor = dbcon.cursor()

        self.cursor.execute("TRUNCATE TFs")
        self.cursor.execute("TRUNCATE IDFs")
        self.cursor.execute("TRUNCATE words")
        self.cursor.execute("TRUNCATE documents")

        # Get pages from the database
        self.cursor.execute(
            """
            SELECT link, content FROM crawled
        """
        )
        self.pages = self.cursor.fetchall()

    def __del__(self):
        if hasattr(self, "cursor"):
            self.cursor.close()

    async def process(self):
        """
        Loads the BeautifulSoup object from a file, one at a time.
        """

        # Add the pages to the task queue
        while self.pages:
            link, blob = self.pages.pop()

            soup = pickle.loads(lzma.decompress(blob))
            if soup is not None:
                await self.propagate_to_next(soup, link)

            print(f"Loaded {link}: {soup.title.string if soup.title else 'No title'}")
