import gensim.downloader as api
import gensim
import time

model = None

def most_similar(word, topn=7)-> list:
    global model
    if model is None:
        try:
            model = gensim.models.KeyedVectors.load('./glove-wiki-gigaword-100.model')
        except FileNotFoundError:
            print("Model not found, will dowonload it")
            model = api.load('glove-wiki-gigaword-100')
            model.save('glove-wiki-gigaword-100.model')
            print("Model downloaded and saved")
    try:

        most_sim = model.most_similar(word, topn=topn)
        print(f"Most similar words to {word}: {most_sim}")
        return most_sim
    except Exception:
        return []

# Example query

print(most_similar("tiger"))