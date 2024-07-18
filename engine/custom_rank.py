import pandas as pd

from custom_db import get_doc_by_id, load_pages
from sklearn.feature_extraction.text import TfidfVectorizer

from tokenizer import process_text
from custom_db import index_pages, get_num_docs, get_average_document_length, get_idf, get_tf

from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

def preprocess_query(Q):
    tokenized_query = process_text(Q)
    return tokenized_query


def find_intersection_2(Q):
    df_inverted = pd.read_csv("inverted_index.csv", sep=",", index_col=1)
    df_inverted.drop(columns=["Unnamed: 0"], inplace=True)

    # df_inverted.set_index("word", inplace=True)
    print(df_inverted.columns)
    print(df_inverted.head())
    tokenized_query = preprocess_query(Q)
    print(tokenized_query)
    result = []
    for token in tokenized_query:
        if token in df_inverted.word.values:
            print(f"Found token: {token}")
            doc_ids = df_inverted[df_inverted["word"] == token]["doc_ids"].apply(eval)
            print(f"It has {len(doc_ids)} doc_ids")
            result.append(doc_ids)
    # print(f"result: {result}")
    # find intersection of all lists in result
    intersection = set(result[0]).intersection(*result)
    return intersection


def find_documents(Q) -> set:
    df_inverted = pd.read_csv("inverted_index.csv", converters={'doc_ids': pd.eval})
    df_inverted.set_index("word", inplace=True)
    df_inverted.drop(columns=["Unnamed: 0"], inplace=True)

    print(df_inverted.head())
    tokenized_query = preprocess_query(Q)
    print(df_inverted.index.values)
    result = []
    for token in tokenized_query:
        if token in df_inverted.index.values:
            print(f"Found token: {token}")
            doc_ids = df_inverted.loc[token].doc_ids
            print(f"It has {len(doc_ids)} doc_ids")
            result.append(doc_ids)
    # find intersection of all lists in result
    intersection = set(result[0]).intersection(*result)
    union = set(result[0]).union(*result)
    if len(intersection) < 2:
        print("No intersection found")
        return union
    return intersection


def dummy_tokenizer(tokens: list[str]):
    return tokens


def generate_tf_idf_matrix():
    df = load_pages()
    if df is None:
        return pd.DataFrame()
    df_text = df["tokenized_text"]
    # create list of lists containing the tokenized text
    tokenized_text = []
    vectorizer = TfidfVectorizer(tokenizer=dummy_tokenizer, preprocessor=dummy_tokenizer, token_pattern=None)
    X = vectorizer.fit_transform(df_text.values)
    features = pd.DataFrame(X.todense(), columns=vectorizer.get_feature_names_out())

    return features





def rank_documents(subset_D, Q, X):
    # Filter the DataFrame to include only the documents in subset_D
    subset_adj = [x - 1 for x in subset_D]
    filtered_X = X.loc[list(subset_adj)]  # here accessen wir rows

    # Ensure Q is a list of query terms
    query_terms = preprocess_query(Q)
    query_terms_in_X = [term for term in query_terms if term in X.columns]
    # Filter the DataFrame to include only the columns corresponding to the query terms
    if not query_terms_in_X:
        print("No query terms found in the TF-IDF matrix.")
        return pd.DataFrame()
    filtered_X_query_terms = filtered_X[query_terms_in_X]  # here accessen wir ganze columns

    # Sum the TF-IDF values for each document
    filtered_X['sum_tfidf'] = filtered_X_query_terms.sum(axis=1)

    # Rank the documents by the summed TF-IDF values in descending order
    ranked_docs = filtered_X.sort_values(by='sum_tfidf', ascending=False)

    # Map document ID to document with title, URL, and snippet
    ranking = []
    for index, ranked_doc in ranked_docs.iterrows():
        score = ranked_doc['sum_tfidf']

        doc = get_doc_by_id(index)
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


# query = "food and drink"
# docs = find_documents(query)
X = generate_tf_idf_matrix()

def bm_25(subset_D, Q):
    print("Hier in bm25")
    b=0.75
    k=1.5
    avgd = get_average_document_length()
    N = get_num_docs()
    subset_adj = [x - 1 for x in subset_D]
    query_terms = preprocess_query(Q)
    ranking = []
    for doc_id in subset_adj:
        score = 0
        for term in query_terms:
            tf = get_tf(doc_id, term)
            idf = get_idf(term)
            numerator = tf * (k + 1)
            denominator = tf + k * (1 - b + b * N / avgd)
            score += idf * numerator / denominator

        # calculation finished, append to ranking    
        doc = get_doc_by_id(doc_id)
        title = str(doc['title'].values[0]) if not doc.empty else ""
        url = str(doc['url'].values[0]) if not doc.empty else ""
        snippet = str(doc['snippet'].values[0]) if not doc.empty else ""
        result = {
             "id": doc_id,
            "title": title,
            "url": url,
            "description": snippet if snippet else "",
            "summary": "",
            "score": score
        }
        ranking.append(result)
    
    return ranking
            

# print(f"Found {len(docs)} documents, they look like this: {docs}")
# print(f"Result: {generate_tf_idf_matrix('pages.csv')}")

# ranked_docs = rank_documents(docs, query, X)
# print(f"Best 20 docs: {ranked_docs[:20]}")

def rank(query):
    docs = find_documents(query)
    return bm_25(docs, query)


def rank_from_file(filepath: str) -> list[list]:
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
