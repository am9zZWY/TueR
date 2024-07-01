from .crawl import start_crawl


class Document:
    def __init__(self, content: str, title: str, url: str):
        self.content = content
        self.title = title
        self.url = url


class Index:
    def __init__(self):
        self.documents = []

    def add_document(self, document: Document):
        self.documents.append(document)

    def search(self, query: str) -> list[Document]:
        pass


class SearchEngine:
    def __init__(self, index: Index):
        self.index = index

    def crawl(self):
        start_crawl()

    def search(self, query: str) -> list[Document]:
        # TODO: Implement search
        pass
