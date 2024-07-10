import nltk as nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import re
# We have to name this file something else then tokenizer.py because otherweise there will be a conflict with the beautifoul soup tokenizer
# and/or nltk tokenizer
from nltk.corpus import stopwords
import re
import nltk

def remove_punctuations(text):
    punct_tag = re.compile(r'[^\w\s]')
    text = punct_tag.sub(r'', text)
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

def stem_and_remove_stopwords(words):
    # use english porterStemmer

    stemmer = nltk.stem.porter.PorterStemmer()
    words = [stemmer.stem(word) for word in words if word not in stopwords.words("english")] # added stemmer
    return words



def tokenize_data(data):
    """
    Tokenizes the input data.
    """
    pipeline = [remove_punctuations, remove_html, remove_url, remove_emoji, tokenize_plain_words, stem_and_remove_stopwords]
    for pipe in pipeline:
        data = pipe(data)
    print("We are done here in tokenizing")
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
    print(f"Feature names: {feature_names}")
    print(f"X sieht so aus: {X}")
    print(f"Shape of X: {X.shape}")
    print(f"Summe: {X.sum(axis=0)}")
    top_30_words = sorted(zip(feature_names, X.sum(axis=0).tolist()[0]), key=lambda x: x[1], reverse=True)[:30]
    return top_30_words
