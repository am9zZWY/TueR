import duckdb

from pipeline import PipelineElement

summary = None


class Summary:
    def __init__(self, summary_model: str = "google/pegasus-xsum"):
        # Load summarization pipeline
        from transformers import pipeline

        self.summary_model = summary_model
        print(f"Loading summarization model {summary_model}... This may take a few minutes.")
        self.summarizer_pipeline = pipeline("summarization", model=summary_model, tokenizer=summary_model)

    def summarize_text(self, text: str, max_words: int = 15) -> str:
        # Summarize the text
        summarized_text = \
            self.summarizer_pipeline(text, max_length=max_words * 2, min_length=max_words, do_sample=False)[0][
                'summary_text']

        # Truncate to the specified number of words
        words = summarized_text.split()
        if len(words) > max_words:
            summarized_text = ' '.join(words[:max_words]) + '...'

        return summarized_text


def initialize_summary_model():
    global summary
    if summary is None:
        summary = Summary()


def get_summary_model():
    global summary
    initialize_summary_model()
    return summary


class Summarizer(PipelineElement):
    """
    Summarizes the input text.
    """

    def __init__(self, dbcon: duckdb.DuckDBPyConnection):
        super().__init__("Summarizer")
        self.cursor = dbcon.cursor()

        # Load summarization pipeline
        global summary
        initialize_summary_model()
        self.summary = summary

    def __del__(self):
        self.cursor.close()

    async def process(self, data, doc_id, link):
        """
        Summarizes the input text.
        """

        soup = data
        if soup is None:
            print(f"Failed to summarize {link} because the data was empty.")
            return

        # Get the text from the main content
        main_content = soup.find("main") or soup.find("article") or soup.find("section") or soup.find("body")

        if main_content is None:
            print(f"Warning: No main content found for {link}. Using entire body.")
            main_content = soup

        # Summarize the text
        text = main_content.get_text()
        summarized_text = self.summary.summarize_text(text)

        self.cursor.execute("""
            UPDATE documents
            ON     summary = ?
            WHERE  id = ?
        """, [summarized_text, doc_id])

        print(f"Summarized {link} to: {summarized_text}")

        if not self.is_shutdown():
            await self.propagate_to_next(summarized_text)
