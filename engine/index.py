import logging

from custom_db import upsert_page_to_index, add_title_to_index, add_snippet_to_index, load_pages
from pipeline import PipelineElement


class Indexer(PipelineElement):
    """
    Adds the data to the index.
    """

    def __init__(self):
        super().__init__("Indexer")

        self._load_state()

    async def process(self, data, link):
        """
        Indexes the input data.
        """

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

        # Add more data to the index
        upsert_page_to_index(url=link)
        add_title_to_index(url=link, title=title_content)
        add_snippet_to_index(url=link, snippet=description_content)

        print(f"Indexed {link}")
        if not self.is_shutdown():
            await self.call_next(soup, link)

    def _load_state(self):
        """
        Load the state of the indexer.
        """

        # TODO: Not ideal! This should be in a database
        load_pages()
