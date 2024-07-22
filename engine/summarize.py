summary = None  # Global accessor for summary model


class Summary:
    def __init__(self, summary_model: str = "google/pegasus-xsum"):
        # Load summarization pipeline
        from transformers import pipeline

        self.summary_model = summary_model
        print(
            f"Loading summarization model {summary_model}... This may take a few minutes."
        )
        self.summarizer_pipeline = pipeline(
            "summarization", model=summary_model, tokenizer=summary_model
        )

    def summarize_text(self, text: str, max_words: int = 15) -> str:
        # Summarize the text
        summarized_text = self.summarizer_pipeline(
            text, max_length=max_words * 2, min_length=max_words, do_sample=False
        )[0]["summary_text"]

        # Truncate to the specified number of words
        words = summarized_text.split()
        if len(words) > max_words:
            summarized_text = " ".join(words[:max_words]) + "..."

        return summarized_text


def get_summary_model() -> Summary:
    """
    Get or initialize summarization model
    """
    global summary
    if summary is None:
        summary = Summary()
    return summary
