"""
Pipeline for Crawling, Tokenizing, and Indexing
"""
from crawl import start_crawl
from custom_db import index_pages, access_index, save_pages

if __name__ == "__main__":
    start_crawl()  # in crawling, we also tokenize
    # TODO: seperate crawling and tokenizing
    index_pages()
    index_df = access_index()
    index_df.to_csv("inverted_index.csv")
    save_pages()
