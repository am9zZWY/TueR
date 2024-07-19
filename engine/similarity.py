import gensim.downloader as api
import gensim
import time


# Step 4: Query the model directly
def most_similar(word, topn=7):
    try:
        model = gensim.models.KeyedVectors.load('./glove-wiki-gigaword-100.model')
    except FileNotFoundError:
        model = None
        print("Model not found, will dowonload it")
        model = api.load('glove-wiki-gigaword-100')
        model.save('glove-wiki-gigaword-100.model')
        print("Model downloaded and saved")
    try:
        most_sim = model.most_similar(word, topn=topn)
        print(f"Most similar words to {word}: {most_sim}")
        return most_sim
    except KeyError:
        return []

# Example query
