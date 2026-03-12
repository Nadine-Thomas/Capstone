import pandas as pd
from db import get_db_connection
from config import RECOMMENDATIONS_OUTPUT_FILE, BATCH_SIZE


def upload_recommendations(recommendations_file, batch_size):
    """
    Read the recommendations CSV produced by calculate_recommendations.py
    and insert all rows into the recommendations table.

    The CSV uses group_id / recommended_group_id which matches the DB schema.
    """
    df = pd.read_csv(
        recommendations_file,
        dtype={"group_id": str, "recommended_group_id": str},
    )
    rows = list(df.itertuples(index=False, name=None))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            cursor.executemany(
                "INSERT IGNORE INTO recommendations "
                "(group_id, rec_rank, recommended_group_id, recommended_title, score) "
                "VALUES (%s, %s, %s, %s, %s)",
                batch,
            )
            conn.commit()
            print(f"  Inserted {min(i + batch_size, len(rows)):,}/{len(rows):,} rows")
    except Exception as e:
        conn.rollback()
        raise RuntimeError("Upload failed") from e
    finally:
        cursor.close()
        conn.close()

    print("Done inserting recommendations.")


if __name__ == "__main__":
    upload_recommendations(RECOMMENDATIONS_OUTPUT_FILE, BATCH_SIZE)