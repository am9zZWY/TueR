import pandas as pd

from collections import defaultdict
import re

# Create a DataFrame to store HTML pages
pages_df = pd.DataFrame(columns=['id', 'url', 'tokenized_text'])
inverted_index = defaultdict(list)

def save_html_to_df(url, tokenized_text):
    global pages_df
    new_id = len(pages_df) + 1
    new_row = {'id': new_id, 'url': url, 'tokenized_text': tokenized_text}
    pages_df = pd.concat([pages_df,pd.DataFrame([new_row])], ignore_index=True)


# Create an inverted index

def get_overview():
    return pages_df.head()

def save_pages():
    global pages_df
    pages_df.to_csv("pages.csv")

def add_document_to_index(doc_id, words: list[str]):
    print(f"Adding stuff")
    global inverted_index
    for word_index, word in enumerate(words):
        position = word_index + 1
        # If the word is not in the invertex index, simply add it
        if word not in inverted_index:
            print(f"Adding new word {word}")
            inverted_index[word] = [[doc_id, [position]]]
        else:
            # There are two cases.
            # The word is in the inverted index:
            # - but the document is not in the list
            # - and the document is in the list but the position is not

            # Check if the document is in the list
            doc_ids = [doc[0] for doc in inverted_index[word]]

            if doc_id not in doc_ids:
                print(f"Adding new document {doc_id} to word {word}")
                inverted_index[word].append([doc_id, [position]])
            else:
                # The document is in the list, but the position is not
                # Get the index of the document
                doc_index = doc_ids.index(doc_id)
                # Check if the position is in the list
                if position not in inverted_index[word][doc_index][1]:
                    print(f"Adding new position {position} to word {word} in document {doc_id}")
                    inverted_index[word][doc_index][1].append(position)


def index_pages():
    for index, row in pages_df.iterrows():

        add_document_to_index(row['id'], row['tokenized_text'])


def access_index():
    index_df = pd.DataFrame(list(inverted_index.items()), columns=['word', 'doc_ids'])
    return index_df


# Convert the inverted index to a DataFrame
