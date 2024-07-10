import nltk as nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import re
# We have to name this file something else then tokenizer.py because otherweise there will be a conflict with the beautifoul soup tokenizer
# and/or nltk tokenizer


def tokenize_data(data):
    """
    Tokenizes the input data.
    """
    # delete whitespaces
    text = data.strip()
    text = re.sub(r'\s+', ' ', text)
    # Split the data into words
    print(f"Text: {text}")
    words = nltk.word_tokenize(text)
    return words


def tf_idf_vectorize(data):
    """
    Vectorizes the input data using the TF-IDF algorithm.
    """
    # Create the vectorizer
    vectorizer = TfidfVectorizer(tokenizer=tokenize_data, stop_words="english")
    # Vectorize the data
    X = vectorizer.fit_transform(data)
    return X

def top_30_words(data):
    """
    Returns the top 30 words from the input data.
    """
    # Create the vectorizer
    vectorizer = TfidfVectorizer(tokenizer=tokenize_data, stop_words="english")
    # Vectorize the data
    X = vectorizer.fit_transform(data)
    # Get the feature names
    feature_names = vectorizer.get_feature_names_out()
    # print(f"Feature names: {feature_names}")
    # print(f"X sieht so aus: {X}")
    # print(f"Shape of X: {X.shape}")
    # print(f"Summe: {X.sum(axis=0)}")
    top_30_words = sorted(zip(feature_names, X.sum(axis=0).tolist()[0]), key=lambda x: x[1], reverse=True)[:30]
    return top_30_words
