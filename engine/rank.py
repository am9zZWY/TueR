
import math
from collections import Counter, defaultdict
from functools import lru_cache
import bisect
import numpy as np
from custom_db import get_tokens, load_pages, get_page_by_id
from tokenizer import process_and_expand_query
import pandas as pd
load_pages()

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


tf = TF()


def IDF():
    """
    Estimate inverse document frequencies based on a corpus of documents.
    """
    global tokens

    return np.array([math.log(len(tokens) / sum(col)) for col in zip(*tf)])


idf = IDF()




def find_documents(query) -> set:
    df_inverted = pd.read_csv("inverted_index.csv", converters={'doc_ids': pd.eval})
    df_inverted.set_index("word", inplace=True)
    df_inverted.drop(columns=["Unnamed: 0"], inplace=True)
    result = []
    for token in query:
        if token in df_inverted.index.values:
            doc_ids = df_inverted.loc[token].doc_ids
            result.append(doc_ids)
    intersection = set(result[0]).intersection(*result)
    if len(intersection) < 2:
        return set(result[0]).union(*result)
    return intersection


def bm25(query: str, k1=1.5, b=0.75):
    """
    Rank documents by BM25.
    """
    global tokens, tf, idf, bow

    # Create the query vector
    
    query, expanded_query = process_and_expand_query(query)
    # Calculate the BM25 scores
    scores = []
    L = len(tokens)  # TODO: Average document length
    for index, doc in enumerate(tokens):
        L_d = len(doc)
        score = 0
        for word in query:
            if word not in bow:
                continue
            weight = 1 if word in expanded_query.keys() else 4
            
            i = bow.index(word)
            idf_val = idf[i]
            tf_val = tf[index][i]
            # if tf_val != 0:
            #     # print(f"tf_val: {tf_val}")
            score += weight * idf_val * (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * L_d / L))
        for sims in expanded_query.values():
            for word, weight in sims:
                if weight < 0.7:
                    continue
                if word not in bow:
                    continue
                i = bow.index(word)
                idf_val = idf[i]
                tf_val = tf[index][i]
                # if tf_val != 0:
                #     # print(f"tf_val: {tf_val}")
                score += weight/3 * (idf_val * (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * L_d / L)))
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
        bisect.insort(ranking, result, key=lambda x: -1* x['score'])

    return ranking


def rank(query):
    return bm25(query)


res = rank("Tübingen publications")
print(res[:10])