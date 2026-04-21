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

    works_rows = [
        (row.group_id, row.title, row.author_id)
        for row in books.itertuples(index=False)
    ]

    # Eplode the book_ids list into separate rows for the editions table
    books_exploded = books.explode("book_ids").rename(columns={"book_ids": "book_id"})
    books_exploded["book_id"] = books_exploded["book_id"].astype(str)

    editions_rows = [
        (row.book_id, row.group_id)
        for row in books_exploded.itertuples(index=False)
        if row.book_id  # skip any empty book_id values
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # First insert works (one row per work, with group_id as primary key).
        for i in range(0, len(works_rows), batch_size):
            batch = works_rows[i:i + batch_size]
            cursor.executemany(
                "INSERT IGNORE INTO works (group_id, title, author_id) "
                "VALUES (%s, %s, %s)",
                batch,
            )
            conn.commit()
            print(f"  Works inserted: {min(i + batch_size, len(works_rows)):,}/{len(works_rows):,}")
    
        # Then insert editions.
        for i in range(0, len(editions_rows), batch_size):
            batch = editions_rows[i:i + batch_size]
            cursor.executemany(
                "INSERT IGNORE INTO editions (book_id, group_id) "
                "VALUES (%s, %s)",
                batch,
            )
            conn.commit()
            print(f"  Editions inserted: {min(i + batch_size, len(editions_rows)):,}"
                  f"/{len(editions_rows):,}")
 
    except Exception as e:
        conn.rollback()
        raise RuntimeError("Upload failed") from e
    finally:
        cursor.close()
        conn.close()

    print("Done inserting books.")


if __name__ == "__main__":
    upload_books(BOOKS_OUTPUT_FILE, BATCH_SIZE)