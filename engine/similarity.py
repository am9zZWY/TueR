import gensim.downloader as api
import gensim
import time


# Step 4: Query the model directly
def most_similar(word, topn=10):
    try:
        model = gensim.models.KeyedVectors.load('./glove-wiki-gigaword-100.model')
    except FileNotFoundError:
        model = None
        print("Model not found, will dowonload it")
        model = api.load('glove-wiki-gigaword-100')
        model.save('glove-wiki-gigaword-100.model')
        print("Model downloaded and saved")
    try:
        return model.most_similar(word, topn=topn)
    except KeyError:
        return []

# Example query
start_time = time.time()
similar_words = most_similar('juice', topn=10)
print(similar_words)
print(f"Duration: {time.time() - start_time}")
