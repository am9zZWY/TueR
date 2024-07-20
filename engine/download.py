import lzma
import pickle

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

from pipeline import PipelineElement


class Downloader(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection, storage_dir='downloads'):
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
            [link, lzma.compress(pickle.dumps(data))])


class Loader(PipelineElement):
    def __init__(self, dbcon: duckdb.DuckDBPyConnection, storage_dir='downloads'):
        super().__init__("Loader")
        self.cursor = dbcon.cursor()

    def __del__(self):
        self.cursor.close()

    async def process(self):
        """
        Loads the BeautifulSoup object from a file, one at a time.
        """

        self.cursor.execute("""
            SELECT link, blob FROM crawled
        """)

        self.cursor.execute("TRUNCATE documents")
        self.cursor.execute("TRUNCATE words")
        self.cursor.execute("TRUNCATE TFs")
        self.cursor.execute("TRUNCATE IDFs")

        row = self.cursor.fetchone()
        while row:
            link, blob = row

            soup = pickle.loads(lzma.decompress(blob))

            await self.propagate_to_next(soup, link)

            row = self.cursor.fetchone()

