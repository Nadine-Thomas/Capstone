import pandas as pd
from db import get_db_connection
from config import BOOKS_OUTPUT_FILE, BATCH_SIZE


def upload_books(books_file, batch_size):
    """
    Read the cleaned books file and insert every edition into the books table.
    All editions of the same work share a group_id so that recommendations
    (stored at the group level) can be joined back to any edition.
    """
    books = pd.read_json(books_file, lines=True)

    # Initialize group_id column
    books["group_id"] = books.index.astype(str)

    # One row per edition
    books_exploded = books.explode("book_ids").rename(columns={"book_ids": "book_id"})
    books_exploded["book_id"] = books_exploded["book_id"].astype(str)

    book_id_to_title  = books_exploded.set_index("book_id")["title"].to_dict()
    book_id_to_group  = books_exploded.set_index("book_id")["group_id"].to_dict()
    book_id_to_author = books_exploded.set_index("book_id")["author_id"].to_dict()

    rows = [
        (bid, book_id_to_title[bid], book_id_to_group[bid], book_id_to_author[bid])
        for bid in book_id_to_title
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            cursor.executemany(
                "INSERT IGNORE INTO books (book_id, title, group_id, author_id) "
                "VALUES (%s, %s, %s, %s)",
                batch,
            )
            conn.commit()
            print(f"  Books inserted: {min(i + batch_size, len(rows)):,}/{len(rows):,}")
    except Exception as e:
        conn.rollback()
        raise RuntimeError("Upload failed") from e
    finally:
        cursor.close()
        conn.close()

    print("Done inserting books.")


if __name__ == "__main__":
    upload_books(BOOKS_OUTPUT_FILE, BATCH_SIZE)