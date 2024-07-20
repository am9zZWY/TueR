import duckdb

from custom_db import load_pages
from pipeline import PipelineElement


class Indexer(PipelineElement):
    """
    Adds the data to the index.
    """

    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Indexer")

        self.cursor = dbcon.cursor()

    def __del__(self):
        self.cursor.close()

    async def process(self, data, link):
        """
        Indexes the input data.
        """
        print(f"Indexing {link}")

        if data is None:
            print(f"Failed to index {link} because the data was empty.")
            return

        soup = data

        # Title
        title = soup.find("title")
        title_content = title.string if title is not None else ""

        # Snippet or description
        description = soup.find("meta", attrs={"name": "description"})
        description_content = description.get("content") if description is not None else ""

        self.cursor.execute("""
            INSERT INTO documents(link, title, description)
            VALUES (?, ?, ?)
        """, [link, title_content, description_content])

        doc_id = self.cursor.execute("""
            SELECT id FROM documents WHERE link = ?
        """, [link]).fetchone()[0]

        if not self.is_shutdown():
            await self.propagate_to_next(soup, doc_id, link)
