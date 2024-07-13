import re
import math
from typing import List

import numpy as np

from custom_db import get_tokens, load_pages


def voc(tokens: list[list[str]]) -> list[str]:
    """
    Create a vocabulary from a list of tokens.
    """
    return sorted(set([word for doc in tokens for word in doc]))


def TF(tokens: list[list[str]]) -> list[list[int]]:
    """
    Turn a corpus of arbitrary texts into term-frequency weighted BOW vectors.
    """

    # Create BOW
    bow = voc(tokens)

    # BOW vectors
    bow_vectors = [[]] * len(tokens)
    # Iterate the corpus
    for index, doc in enumerate(tokens):
        # Create vector the size of BOW
        bow_vectors[index] = [0] * len(bow)
        # Iterate the documents
        for sent in doc:
            for word in sent.split():
                # Find the cleaned word in the BOW and count up the frequency
                bow_vectors[index][bow.index(word)] += 1

    return bow_vectors


def IDF(tokens: list[list[str]]):
    """
    Estimate inverse document frequencies based on a corpus of documents.
    """

    return np.array([math.log(len(tokens) / sum(col)) for col in zip(*TF(tokens))])


def bm25(tokens: list[list[str]], query: str, k1=1.5, b=0.75):
    """
    Rank documents by BM25.
    """

    bow = voc(tokens)

    # Create the IDF vector
    idf = IDF(tokens)

    # Create the TF matrix
    tf = TF(tokens)

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

    # Add document IDs to the scores
    scores = list(zip(range(len(tokens)), scores))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    return scores


def rank(query):
    load_pages()
    tokens = get_tokens()
    return bm25(tokens, query)
