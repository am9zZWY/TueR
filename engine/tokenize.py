import nltk as nltk

def tokenize_data(data):
    """
    Tokenizes the input data.
    """
    # Split the data into words
    words = nltk.word_tokenize(data)
    return words