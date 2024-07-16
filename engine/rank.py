import logging
import math
from collections import Counter, defaultdict
from functools import lru_cache

import numpy as np
from custom_db import get_tokens, load_pages, get_page_by_id

load_pages()

logging.info("Getting tokens...")
tokens = get_tokens()


@lru_cache(maxsize=None)
def BOW() -> list[str]:
    """
    Create a vocabulary from a list of tokens.
    """
    global tokens
    return sorted(set([word for doc in tokens for word in doc]))


bow = BOW()


def TF() -> np.ndarray:
    """
    Turn a corpus of arbitrary texts into term-frequency weighted BOW vectors.
    """
    global tokens, bow

    # Create a dictionary for faster lookups
    bow_dict = {word: idx for idx, word in enumerate(bow)}

    # Precompute word frequencies for each document
    doc_word_counts = [Counter(doc) for doc in tokens]

    # Create BOW vectors using NumPy
    bow_vectors = np.zeros((len(tokens), len(bow)), dtype=int)

    for doc_idx, word_counts in enumerate(doc_word_counts):
        for word, count in word_counts.items():
            if word in bow_dict:
                bow_vectors[doc_idx, bow_dict[word]] = count

    return bow_vectors


logging.info("Getting TF...")
tf = TF()


def IDF():
    """
    Estimate inverse document frequencies based on a corpus of documents.
    """
    global tokens

    return np.array([math.log(len(tokens) / sum(col)) for col in zip(*tf)])


logging.info("Getting IDF...")
idf = IDF()

logging.info("Ready!")


def bm25(query: str, k1=1.5, b=0.75):
    """
    Rank documents by BM25.
    """
    global tokens, tf, idf, bow

    # Create the query vector
    query_vector = [0] * len(bow)
    for word in query.split():
        query_vector[bow.index(word)] += 1

    # Calculate the BM25 scores
    scores = []
    for index, doc in enumerate(tokens):
        score = 0
        for word in query.split():
            i = bow.index(word)
            score += idf[i] * (tf[index][i] * (k1 + 1)) / (tf[index][i] + k1 * (1 - b + b * len(doc) / len(tokens)))
        scores.append(score)

    # Map document ID to document with title, URL, and snippet
    ranking = []
    for index, score in enumerate(scores):
        doc = get_page_by_id(index)

        title = str(doc['title'].values[0]) if not doc.empty else ""
        url = str(doc['url'].values[0]) if not doc.empty else ""
        snippet = str(doc['snippet'].values[0]) if not doc.empty else ""

        result = {
            "id": index,
            "title": title,
            "url": url,
            "description": snippet if snippet else "",
            "summary": "",
            "score": score
        }
        ranking.append(result)

    return ranking


def rank(query):
    return bm25(query)
