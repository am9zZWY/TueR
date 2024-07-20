import duckdb
from tokenizer import process_and_expand_query
import pandas as pd


def bm25(query: str, dbcon: duckdb.DuckDBPyConnection, k1=1.5, b=0.75, debug: bool = False):
    """
    Rank documents by BM25.
    """

    # Create the query vector
    query, expanded_query = process_and_expand_query(query)

    # flatten expanded query terms
    sim_weight_list = [(word, score)
                       for sim_list in expanded_query.values()
                       for word, score in sim_list
                       if score > 0.7 and word not in query]

    # Search terms to look up tf and idf for
    search_terms = set(query).union(set(map(lambda x: x[0], sim_weight_list)))

    if debug:
        print(f"expanded_query: {expanded_query}")
        print(f"db_query: {search_terms}")
        print(f"Query: {query}")

    con = dbcon  # Rename DB connection

    # DataFrame to directly query in DuckDB
    df_search = pd.DataFrame(sorted(search_terms), columns=['search_terms'])

    # Query TF and IDf for desired search terms
    df_tf = con.execute("""
        SELECT t.doc, w.word, t.amount
        FROM   tfs AS t, words AS w, df_search AS _(token)
        WHERE  w.word = token AND w.id = t.word;
    """).df().set_index(['doc', 'word'])['amount']

    df_idf = con.execute("""
        SELECT w.word, i.idf
        FROM   idfs AS i, words AS w, df_search AS _(token)
        WHERE  w.word = token AND w.id = i.word;
    """).df().set_index(['word'])['idf']

    # Calculate the BM25 scores
    scores = []

    L = con.execute("SELECT COUNT(*) FROM documents").fetchall()[0][0]

    # Iterate over documents
    for doc_id in df_tf.index.get_level_values('doc').unique().tolist():
        doc_tf = df_tf.loc[doc_id]

        # Get words found for document
        words = set(doc_tf.index.get_level_values('word').tolist())
        L_d = len(words)

        score = 0

        # Calculate "classic" BM25 for only query terms
        for word in set(query).intersection(words):
            weight = 4 if not expanded_query[word] else 1  # weight synonym-less words higher

            idf_val = df_idf[word]
            tf_val = doc_tf[word]

            score += weight * idf_val * (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * L_d / L))

        # Calculate BM25 for expanded query terms
        for synonym, weight in filter(lambda x: x[0] in words, sim_weight_list):
            idf_val = df_idf[synonym]
            tf_val = doc_tf[synonym]

            score += weight / 3 * (idf_val * (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * L_d / L)))

        scores.append((doc_id, score))

    # Retrieve Document information from DB in ranked fashion
    df_scores = pd.DataFrame(scores, columns=['doc', 'score'])
    ranking = con.execute("""
        SELECT d.id AS id, d.title AS title, d.link AS url, 
               d.description AS description, d.summary AS summary, 
               s.score AS score
        FROM   documents AS d, df_scores AS s
        WHERE  d.id = s.doc
        ORDER BY s.score DESC
    """).df().to_dict('records')

    con.close()

    return ranking


def rank(query: str, debug: bool = False):
    """
    Rank the documents according to the query.
    Args:
        query:
        debug:

    Returns:

    """
    con = duckdb.connect('crawlies.db')
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
    return [rank(query) for query in queries]


if __name__ == '__main__':
    res = rank("food an drink", debug=True)
    print(res[:10])
    res = rank("Tübingen publications", debug=True)
    print(res[:10])
