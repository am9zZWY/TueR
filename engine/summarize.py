from eld import LanguageDetector
from transformers import pipeline
from bs4 import BeautifulSoup

from tokenizer import remove_unicode

# Language detector
LANG_DETECTOR = LanguageDetector()

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

    def summarize_text(self, text: str, max_words: int = 20) -> str:
        if not text:
            return "No text provided for summarization."

        summarized_text = self.summarizer_pipeline(
            text, max_length=max_words * 2, min_length=max_words, do_sample=False
        )[0]["summary_text"]

        words = summarized_text.split()
        return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

    def summarize_soup(self, soup: BeautifulSoup, max_words: int = 20) -> str:
        if not isinstance(soup, BeautifulSoup):
            return "Invalid input: Expected a BeautifulSoup object."

        main_content = soup.find("body")
        meta_description = soup.find("meta", attrs={"name": "description"})

        text = ""
        if main_content:
            text = main_content.get_text(strip=True)
        elif meta_description and "content" in meta_description.attrs:
            text = meta_description["content"]

        text = text[:512]  # Limit to 512 characters

        if len(text) < 40:
            return "Insufficient content for summarization."

        text = remove_unicode(text)

        print(f"Summarizing text: {text[:100]}... (length: {len(text)})")
        return self.summarize_text(text, max_words)


def get_summary_model() -> Summary:
    """
    Get or initialize summarization model
    """
    global summary
    if summary is None:
        summary = Summary()
    return summary
