# file to test the written functions

from custom_tokenizer import tokenize_data, tf_idf_vectorize, top_30_words

CUSTOM_TEXT = "Lorem Ipsum is simply dummy text" + "       " +  "  \n     "+ "of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

top_30_words = top_30_words([CUSTOM_TEXT])
print(top_30_words)
