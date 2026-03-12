import gzip
import json
from config import BOOKS_INPUT_FILE, BOOKS_OUTPUT_FILE

def clean_books(input_file, output_file):
    """
    Read the raw Goodreads books file, group all editions of the same work under
    a single entry keyed by work_id, and write only English works.
    """

    # Initialize dictionary that holds grouped book editions
    books = {}

    with gzip.open(input_file, "rt", encoding="utf-8") as infile:
        for line in infile:
            data = json.loads(line)

            work_id = data.get("work_id")
            if not work_id:
                continue

            # Get book information if available 
            book_id = data.get("book_id", "")
            reviews = data.get("text_reviews_count", 0)
            language = data.get("language_code", "")
            title = data.get("title_without_series") or data.get("title", "")
            is_english = language == "eng"

            authors = data.get("authors", [])
            author_id = authors[0]["author_id"] if authors else ""

            # If work_id is not yet in books, create a new entry for this work
            if work_id not in books:
                books[work_id] = {
                    "book_ids": [book_id] if book_id else [],
                    "title": title,
                    "author_id": author_id,
                    "text_reviews_count": reviews,
                    "has_english": is_english,
                }
            # If book corpus already has work_id add book_id and reviews
            else:
                if book_id:
                    books[work_id]["book_ids"].append(book_id)
                books[work_id]["text_reviews_count"] += reviews
                # Make sure English book title is the title for work_id
                if is_english and title:
                    books[work_id]["title"] = title
                    books[work_id]["has_english"] = True

    with gzip.open(output_file, "wt", encoding="utf-8") as outfile:
        for book in books.values():
            # Only include books with English editions
            if not book["has_english"]:
                continue
            del book["has_english"]

            outfile.write(json.dumps(book, ensure_ascii=False) + "\n")

    print(f"Processing complete! Books written to: {output_file}")

clean_books(BOOKS_INPUT_FILE, BOOKS_OUTPUT_FILE)