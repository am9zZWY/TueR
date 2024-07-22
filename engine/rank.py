import duckdb
import pandas as pd
from similarity import most_similar
import math
from tokenizer import preprocess_text
from nltk.stem import WordNetLemmatizer
import nltk
import spacy

# Download the NLTK data
print("Downloading NLTK data...")
nltk.download('wordnet')

nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "parser", "senter"])

def calc_num_similar_words(query_length: int, max_sim_words=7, decrease_rate=0.08) -> int:
    """Exponential decay function to calculate the number of similar words to use based on the query length.

    Args:
        query_length (int): Query after preprocessing.
        max_sim_words (int, optional): Max number of sim words we want to produce. Represents the baseline. Defaults to 7.
        decrease_rate (float, optional): Rate we want our function to decrease. The bigger the number the higher the decrease. Defaults to 0.08.

    Returns:
        int: _description_
    """
    num_sim_words = max_sim_words * math.exp(-decrease_rate * query_length)
    return int(num_sim_words)

def process_and_expand_query(query: str)->tuple:
    """Preprocess the query and expand it with similar words.

    Args:
        query (str): User query.

    Returns:
        tuple: Preprocessed query and expanded query with similar words and their similarity scores.
    """
    default_num_sim_words = 7
    processed_query = preprocess_text(query)
    doc = nlp(processed_query)
    wnl = WordNetLemmatizer()
    tokens = []

    proccessed_sim_words = {}
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        token = token.lemma_ if token.pos_ in ["NOUN", "PROPN"] else token.text
        tokens.append(token)
    tokens_length = len(tokens)
    if tokens_length > 7:
        num_sim_words = calc_num_similar_words(tokens_length)
    else:   
        num_sim_words = default_num_sim_words
    for token in tokens:
            sim_words = most_similar(token, num_sim_words)
            proccessed_sim_words[token] = list(map(lambda x: (wnl.lemmatize(x[0].lower()), x[1]), sim_words))    
    return tokens, proccessed_sim_words


def bm25(
    query: str, dbcon: duckdb.DuckDBPyConnection, k1=1.5, b=0.75, debug: bool = False
) -> list[dict]:
    """
    Rank documents by BM25. Additionally, use similar words aswell for ranking, however with a lower weight/portion.
    """

    # Create the query vector
    query, expanded_query = process_and_expand_query(query)

    # flatten expanded query terms
    sim_weight_list = [
        (word, score)
        for sim_list in expanded_query.values()
        for word, score in sim_list
        if score > 0.7 and word not in query
    ]

    # Search terms to look up tf and idf for
    search_terms = set(query).union(set(map(lambda x: x[0], sim_weight_list)))

    if debug:
        print(f"expanded_query: {expanded_query}")
        print(f"db_query: {search_terms}")
        print(f"Query: {query}")

    con = dbcon  # Rename DB connection

    # DataFrame to directly query in DuckDB
    df_search = pd.DataFrame(sorted(search_terms), columns=["search_terms"])

    # Query TF and IDf for desired search terms
    df_tf = (
        con.execute(
            """
        SELECT t.doc, w.word, t.tf
        FROM   tfs AS t, words AS w, df_search AS _(token)
        WHERE  w.word = token AND w.id = t.word;
    """
        )
        .df()
        .set_index(["doc", "word"])["tf"]
    )

    df_idf = (
        con.execute(
            """
        SELECT w.word, i.idf
        FROM   idfs AS i, words AS w, df_search AS _(token)
        WHERE  w.word = token AND w.id = i.word;
    """
        )
        .df()
        .set_index(["word"])["idf"]
    )

    scores = []

    L = con.execute("SELECT COUNT(*) FROM documents").fetchall()[0][0]

    # Iterate over documents
    for doc_id in df_tf.index.get_level_values("doc").unique().tolist():
        doc_tf = df_tf.loc[doc_id]

        # Get words found for document
        words = set(doc_tf.index.get_level_values("word").tolist())
        L_d = len(words)

        score = 0

        # Calculate "classic" BM25 for only query terms
        for word in set(query).intersection(words):
            weight = (
                4 if not expanded_query[word] else 1
            )  # weight synonym-less words higher

            idf_val = df_idf[word]
            tf_val = doc_tf[word]

            score += (
                weight
                * idf_val
                * (tf_val * (k1 + 1))
                / (tf_val + k1 * (1 - b + b * L_d / L))
            )

        # Calculate BM25 for expanded query terms with the according weight
        for synonym, weight in filter(lambda x: x[0] in words, sim_weight_list):
            idf_val = df_idf[synonym]
            tf_val = doc_tf[synonym]

            score += (
                weight
                / 3
                * (
                    idf_val
                    * (tf_val * (k1 + 1))
                    / (tf_val + k1 * (1 - b + b * L_d / L))
                )
            )

        scores.append((doc_id, score))

    # Retrieve Document information from DB in ranked fashion
    df_scores = pd.DataFrame(scores, columns=["doc", "score"])
    ranking = (
        con.execute(
            """
        SELECT d.id AS id, d.title AS title, d.link AS url,
               d.description AS description, d.summary AS summary,
               s.score AS score
        FROM   documents AS d, df_scores AS s
        WHERE  d.id = s.doc
        ORDER BY s.score DESC
    """
        )
        .df()
        .to_dict("records")
    )

    con.close()

    return ranking


def rank(query: str, debug: bool = False) -> list[dict]:
    """
    Rank the documents according to the query.
    Args:
        query:
        debug:

    Returns:

    """
    con = duckdb.connect("crawlies.db")
    return bm25(query, con, debug=debug)


def rank_from_file(filepath: str) -> list[list]:
    """
    Rank queries from a file.
    Args:
        filepath:

    Returns:

    """
    queries = []
    with open(filepath, "r") as file:
        content = file.read()

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            number, item = line.split(maxsplit=1)
            queries.append(item)

    # Return the ranked queries
    print("Ranking queries ...")
    rankings = [rank(query) for query in queries]

    # Generate results.txt from rankings
    print("Generating result.txt ...")
    with open("result.txt", "w") as file:
        for i, ranking in enumerate(rankings):
            query_number = i + 1
            for doc in ranking:
                file.write(f'{query_number}\t{doc["id"]}\t{doc["url"]}\t{doc["score"]}\n')
    print("result.txt generated.")
    return rankings


if __name__ == "__main__":
    res = rank("food an drink", debug=True)
    print(res[:10])
    res = rank("Tübingen publications", debug=True)
    print(res[:10])
