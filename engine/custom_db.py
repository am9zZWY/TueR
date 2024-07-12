import pandas as pd

from collections import defaultdict

# Create a DataFrame to store HTML pages
pages_df = pd.DataFrame(columns=['id', 'url', 'tokenized_text'])
inverted_index = defaultdict(list)


def save_html_to_df(url, tokenized_text):
    global pages_df
    new_id = len(pages_df) + 1
    new_row = {'id': new_id, 'url': url, 'tokenized_text': tokenized_text}
    pages_df = pd.concat([pages_df, pd.DataFrame([new_row])], ignore_index=True)


def get_tokens() -> list[list[str]]:
    """
    Get the tokenized text from the pages DataFrame.
    Tokenized text is matrix of tokens.
    One row per document, one column per token.
    Returns: list[list[str]]

    """
    global pages_df
    tokens = pages_df['tokenized_text'].to_list()
    return tokens


# Create an inverted index

def get_overview():
    return pages_df.head()


def add_document_to_index(doc_id, words: list[str]):
    print(f"Adding stuff")
    global inverted_index
    for word in set(words):
        inverted_index[word].append(doc_id)


def index_pages():
    for index, row in pages_df.iterrows():
        add_document_to_index(row['id'], row['tokenized_text'])


def access_index():
    index_df = pd.DataFrame(list(inverted_index.items()), columns=['word', 'doc_ids'])
    return index_df


def save_pages() -> None:
    """
    Save the pages DataFrame to a CSV file.
    Returns: None
    """

    global pages_df
    pages_df.to_csv("pages.csv")


def load_pages() -> pd.DataFrame:
    """
    Load the pages DataFrame from a CSV file.
    Returns: pd.DataFrame
    """

    global pages_df
    pages_df = pd.read_csv("pages.csv")

    # Convert the tokenized_text column to a list of lists
    pages_df['tokenized_text'] = pages_df['tokenized_text'].apply(eval)

    return pages_df
