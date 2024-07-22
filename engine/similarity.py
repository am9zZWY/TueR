import gensim.downloader as api
import gensim
import time

model = None

def most_similar(word: str, topn=7)-> list:
    """Uses GloVe embeddings to find the most similar words to the given word.

    Args:
        word (str): The word to find similar words to.
        topn (int, optional): Amount of similiar words we want to have. Defaults to 7.

    Returns:
        list: A list containing tuples of the most similar words and their similarity score.
    """

    global model
    if model is None:
        try:
            model = gensim.models.KeyedVectors.load('./glove-wiki-gigaword-100.model')
        except FileNotFoundError:
            print("Model not found, downloading...")
            model = api.load('glove-wiki-gigaword-100')
            model.save('glove-wiki-gigaword-100.model')
            print("Model downloaded and saved")
    try:

        most_sim = model.most_similar(word, topn=topn)
        print(f"Most similar words to {word}: {most_sim}")
        return most_sim
    except Exception:
        return []
