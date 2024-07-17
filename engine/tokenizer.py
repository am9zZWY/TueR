import re

import spacy

from custom_db import add_tokens_to_index
from pipeline import PipelineElement
from utils import safe_join, safe_str

"""
IMPORTANT:
Make sure you install the spaCy model with:
python -m spacy download en_core_web_sm
"""


# Define regular expressions for preprocessing

def remove_html(text: str) -> str:
    html_tag = re.compile(r'<.*?>')
    text = html_tag.sub(r'', text)
    return text


def remove_emails(text: str) -> str:
    email_clean = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    text = email_clean.sub(r'', text)
    return text


def remove_percentages(text: str) -> str:
    percentage_clean = re.compile(r"\d+%")
    text = percentage_clean.sub(r'', text)
    return text


def remove_phone_number(text: str) -> str:
    # This pattern matches various phone number formats
    # Thanks to https://stackoverflow.com/a/56450924
    phone_pattern = re.compile(r'''
        ((\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}
    ''', re.VERBOSE)

    # Replace matched phone numbers with an empty string
    text = phone_pattern.sub('', text)
    return text


def remove_dates(text: str) -> str:
    # This pattern matches various date formats
    # Thanks to https://stackoverflow.com/a/8768241
    date_pattern = re.compile(r'''
        ^(?:(?:(?:0?[13578]|1[02])(\/|-|\.)31)\1|(?:(?:0?[1,3-9]|1[0-2])(\/|-|\.)(?:29|30)\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:0?2(\/|-|\.)29\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:(?:0?[1-9])|(?:1[0-2]))(\/|-|\.)(?:0?[1-9]|1\d|2[0-8])\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$
    ''', re.VERBOSE)

    # Replace matched phone numbers with an empty string
    text = date_pattern.sub('', text)
    return text


def remove_times(text: str) -> str:
    # This pattern matches various time formats
    time_pattern = re.compile(r'''
        \b                                  # Word boundary
        (?:
            (?:1[0-2]|0?[1-9])              # Hours: 1-12 with optional leading zero
            :                               # Colon separator
            (?:[0-5][0-9])                  # Minutes: 00-59
            (?:
                :(?:[0-5][0-9])             # Optional seconds: 00-59
                (?:\.[0-9]{1,3})?           # Optional milliseconds
            )?
            \s*(?:AM|PM|am|pm|A\.M\.|P\.M\.)? # Optional AM/PM indicator
        )
        |
            (?:(?:2[0-3]|[01]?[0-9])        # Hours: 00-23
            :                               # Colon separator
            (?:[0-5][0-9])                  # Minutes: 00-59
            (?::(?:[0-5][0-9])              # Optional seconds: 00-59
                (?:\.[0-9]{1,3})?           # Optional milliseconds
            )?
        )
        \b                                  # Word boundary
    ''', re.VERBOSE | re.IGNORECASE)

    # Replace matched times with an empty string
    text = time_pattern.sub('', text)
    return text


def remove_url(text: str) -> str:
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r'', text)
    return text


# Removes Emojis
def remove_emoji(text: str) -> str:
    emoji_clean = re.compile("["
                             u"\U0001F600-\U0001F64F"  # emoticons
                             u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                             u"\U0001F680-\U0001F6FF"  # transport & map symbols
                             u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                             u"\U00002702-\U000027B0"
                             u"\U000024C2-\U0001F251"
                             "]+", flags=re.UNICODE)
    text = emoji_clean.sub(r'', text)
    url_clean = re.compile(r"https://\S+|www\.\S+")
    text = url_clean.sub(r'', text)
    return text


def lower(tokens: list[str]) -> list[str]:
    return [word.lower() for word in tokens]


def preprocess_text(text: str) -> str:
    """Apply all preprocessing steps using regular expressions."""
    text = remove_url(text)
    text = remove_html(text)
    text = remove_emails(text)
    text = remove_times(text)
    text = remove_phone_number(text)
    text = remove_dates(text)
    text = remove_emoji(text)
    text = remove_percentages(text)
    return text


# Load the spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "parser", "senter"])
nlp.add_pipe("merge_entities")
nlp.add_pipe("merge_noun_chunks")


def process_text(text: str) -> list[str]:
    """Process text using spaCy and custom logic."""

    # Preprocess the text
    text = preprocess_text(text)

    # Process with spaCy
    doc = nlp(text)
    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct and not token.is_space]

    # Lowercase the tokens
    tokens = lower(tokens)

    return tokens


class Tokenizer(PipelineElement):
    def __init__(self):
        super().__init__("Tokenizer")

    async def process(self, data, link):
        """
        Tokenizes the input data.
        """

        if data is None:
            print(f"Failed to tokenize {link} because the data was empty.")
            return

        soup = data

        # Get the text from the main content
        main_content = soup.find("main")
        text = main_content.get_text() if main_content is not None else soup.get_text()

        # Get the meta description and title
        description = soup.find("meta", attrs={"name": "description"})
        description_content = description.get("content") if description is not None else ""
        title = soup.find("title")
        title_content = title.string if title is not None else ""

        # Get the alt texts from the images
        img_tags = soup.findAll("img")
        alt_texts = [img.get("alt") for img in img_tags]

        # Join all the text together
        alt_texts_str = safe_join(alt_texts)
        description_str = safe_str(description_content)
        title_str = safe_str(title_content)
        text = f"{text} {alt_texts_str} {description_str} {title_str}".strip()

        # Tokenize the text
        tokenized_text = process_text(text=text)
        add_tokens_to_index(url=link, tokenized_text=tokenized_text)

        print(f"Tokenized text for {link}")


# Test tokenization

test_sentences = [
    "Mr. Smith's car is blue-green.",
    # URLs, emails, prices, and code snippets
    "The URL is https://www.example.com/path?param=value#fragment",
    "She said, 'I can't believe it!'",
    "Send an e-mail to john.doe@example.com",
    "The price is $19.99 (20% off)",
    "I love the movie 'Star Wars: Episode IV - A New Hope'",
    "Python 3.9.5 was released on 05/03/2021",
    "Call me at +1 (555) 123-4567",
    "The equation is E=mc^2",
    "Use the #hashtag and @mention",
    "I'm running... but I'm tired",
    "It's 72°F outside",
    "He said: Don't do that!",
    "The file name is 'document_v1.2.txt'",
    "1,000,000 people can't be wrong",
    "The code is: <html><body>Hello</body></html>",
    "Let's meet at 9:30 AM",
    "The password is: P@ssw0rd!",
    "I'll have a ham & cheese sandwich",
    "The result was 42% (not 50%)",
    # Dates and times
    "The time is 12:34 PM",
    "The time is 12:34:56 PM",
    "The date is 2021-05-03",
    "The time is 12:34:56.789",
    "The time is 12:34:56.789 PM",
    "The time is 23:59",
    "The time is 23:59:59",
    "The time is 23:59:59.999",
    "The time is 23:59:59.999 PM",
    # Named entities
    "I live in New York City",
    "I work at Google",
    "I visited the Statue of Liberty",
    "I went to the United States of America",
    "I flew with Lufthansa",
    "I bought an iPhone",
    "I use Microsoft Windows",
    "Apple Inc. is a great company",
    "I ate at McDonald's",
]

for sentence in test_sentences:
    print(f"Original: {sentence}")
    print(f"Tokenized: {process_text(sentence)}")
    print()
