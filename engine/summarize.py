from transformers import pipeline

from pipeline import PipelineElement


class Summarizer(PipelineElement):
    """
    Summarizes the input text.
    """

    def __init__(self, summary_model: str = "google/pegasus-xsum"):
        super().__init__("Summarizer")

        # Load summarization pipeline
        self.summary_model = summary_model
        print(f"Loading summarization model {summary_model} ... This may take a few minutes.")
        self.summarizer = pipeline("summarization", model=summary_model, tokenizer=summary_model)

    async def process(self, data, link):
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

        text = main_content.get_text()

        summary = self._summarize_text(text)
        print(f"Summarized {link} to: {summary}")

        if not self.is_shutdown():
            await self.propagate_to_next(summary)

    def _summarize_text(self, text: str, max_words: int = 15) -> str:
        summary = self.summarizer(text, max_length=max_words * 2, min_length=max_words, do_sample=False)[0][
            'summary_text']

        # Truncate to the specified number of words
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + '...'

        return summary
