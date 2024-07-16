import logging

import nltk as nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import re
# We have to name this file something else then tokenizer.py because otherweise there will be a conflict with the beautifoul soup tokenizer
# and/or nltk tokenizer
from nltk.corpus import stopwords
import re
import nltk

from custom_db import add_tokens_to_index, upsert_page_to_index, add_title_to_index
from pipeline import PipelineElement
from utils import safe_join, safe_str

WN_LEMMATIZER = nltk.stem.WordNetLemmatizer()
STEMMER = nltk.stem.PorterStemmer()


def remove_punctuations(text):
    # Remove punctuations
    punctuations = re.compile(r'[.!?,;:\-_`´()\[\]{}<>"]')
    text = punctuations.sub(r'', text)
    return text


# Removes HTML syntaxes
def remove_html(text):
    html_tag = re.compile(r'<.*?>')
    text = html_tag.sub(r'', text)
    return text


# Removes URL data
def remove_url(text):
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r'', text)
    return text


# Removes Emojis
def remove_emoji(text):
    emoji_clean = re.compile("["
                             u"\U0001F600-\U0001F64F"  # emoticons
                             u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                             u"\U0001F680-\U0001F6FF"  # transport & map symbols
                             u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                             u"\U00002702-\U000027B0"
                             u"\U000024C2-\U0001F251"
                             "]+", flags=re.UNICODE)
    text = emoji_clean.sub(r'', text)
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r'', text)
    return text


def tokenize_plain_words(words: str):
    return words.split()


def stem(words) -> list[str]:
    words = [STEMMER.stem(word) for word in words]  # added stemmer
    return words


def remove_stopwords(words):
    return [word for word in words if word not in stopwords.words("english")]


def lemmatize(words):
    words = [WN_LEMMATIZER.lemmatize(word) for word in words]
    return words


def tokenize_data(data) -> list[str]:
    """
    Tokenizes the input data.
    """
    pipeline = [remove_punctuations, remove_html, remove_url, remove_emoji, tokenize_plain_words, remove_stopwords,
                lemmatize]
    for pipe in pipeline:
        data = pipe(data)
    return data


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
    logging.info(f"Feature names: {feature_names}")
    logging.info(f"X sieht so aus: {X}")
    logging.info(f"Shape of X: {X.shape}")
    logging.info(f"Summe: {X.sum(axis=0)}")
    top_30_words = sorted(zip(feature_names, X.sum(axis=0).tolist()[0]), key=lambda x: x[1], reverse=True)[:30]
    return top_30_words


class Tokenizer(PipelineElement):
    def __init__(self):
        super().__init__("Tokenizer")

    async def process(self, data, link):
        """
        Tokenizes the input data.
        """

        if data is None:
            logging.info(f"Failed to tokenize {link} because the data was empty.")
            return

        soup = data

        # Get the text from the page
        text = soup.get_text()

        # Get the meta description and title
        description = soup.find("meta", attrs={"name": "description"})
        description_content = description.get("content") if description is not None else ""
        title = soup.find("title")
        title_content = title.string if title is not None else ""

        # Get the alt texts from the images
        img_tags = soup.findAll("img")
        alt_texts = [img.get("alt") for img in img_tags]

        # Join all the text together
        alt_texts_str = safe_join(alt_texts)
        description_str = safe_str(description_content)
        title_str = safe_str(title_content)
        text = f"{text} {alt_texts_str} {description_str} {title_str}".strip()

        # Tokenize the text
        tokenized_text = tokenize_data(data=text)
        add_tokens_to_index(url=link, tokenized_text=tokenized_text)

        logging.info(f"Tokenized text for {link}")
