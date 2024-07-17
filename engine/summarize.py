from gensim.summarization import summarize

# Input text to be summarized
input_text = """
Your input text goes here. It can be a long paragraph or multiple paragraphs. 
"""

# Generate the summary using TextRank algorithm
summary = summarize(input_text, ratio=0.3)  # You can adjust the ratio parameter based on the summary length you desire

# Output the summary
print("Original Text:")
print(input_text)
print("\nSummary:")
print(summary)
