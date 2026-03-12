import gzip
import json
import re
import string

from langdetect import detect, LangDetectException
from nltk.corpus import stopwords

from config import REVIEWS_INPUT_FILE, REVIEWS_OUTPUT_FILE

STOP_WORDS = set(stopwords.words("english"))


def is_english(text):
    """Return True if the text is detected as English."""
    if not text or len(text.strip()) < 10:
        return False
    try:
        return detect(text) == "en"
    except LangDetectException:
        # Fall back to ASCII ratio when detection fails
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
        return ascii_ratio > 0.9
    except Exception:
        return False


def has_link(text):
    """Return True if the text contains a URL."""
    return bool(re.search(r'https?://\S+|www\.\S+|\S+\.com', text))


def clean_text(text):
    """Lowercase, remove numbers and punctuation, and strip stopwords."""
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    return ' '.join(word for word in words if word and word not in STOP_WORDS)


def clean_reviews(input_file, output_file):
    """
    Read the raw Goodreads reviews file, filter and clean each review,
    and write the results to output_file.
    """

    with gzip.open(input_file, "rt", encoding="utf-8") as infile, \
         gzip.open(output_file, "wt", encoding="utf-8") as outfile:

        for line in infile:
            data = json.loads(line)

            # Only keep relevant columns
            review = {
                "book_id": data["book_id"],
                "rating": data["rating"],
                "review_text": data["review_text"],
            }

            # Remove reviews with a rating of 0 because user had not read the book yet
            if review["rating"] == 0:
                continue
            if has_link(review["review_text"]):
                continue
            if not is_english(review["review_text"]):
                continue

            review["review_text"] = clean_text(review["review_text"])
            outfile.write(json.dumps(review, ensure_ascii=False) + "\n")

    print(f"Processing complete! Reviews written to: {output_file}")


if __name__ == "__main__":
    clean_reviews(REVIEWS_INPUT_FILE, REVIEWS_OUTPUT_FILE)