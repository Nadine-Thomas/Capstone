import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from db import get_db_connection

def setup():
    """Create database tables"""
    # Connect to the database 
    conn   = get_db_connection()
    cursor = conn.cursor()

    # Create table works if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            group_id  VARCHAR(50)  NOT NULL,
            title     VARCHAR(500) NOT NULL,
            author_id VARCHAR(50)  NOT NULL,
            PRIMARY KEY (group_id)
        )
    """)

    # Create table editions if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS editions (
            book_id  VARCHAR(50) NOT NULL,
            group_id VARCHAR(50) NOT NULL,
            PRIMARY KEY (book_id),
            CONSTRAINT fk_editions_works
                FOREIGN KEY (group_id) REFERENCES works (group_id)
                ON DELETE CASCADE
        )
    """)

    # Create table recommendations if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            group_id             VARCHAR(50)  NOT NULL,
            rec_rank             TINYINT      NOT NULL,
            recommended_group_id VARCHAR(50)  NOT NULL,
            recommended_title    VARCHAR(500) NOT NULL,
            score                FLOAT        NOT NULL,
            PRIMARY KEY (group_id, rec_rank),
            CONSTRAINT fk_rec_works
                FOREIGN KEY (group_id) REFERENCES works (group_id)
                ON DELETE CASCADE
        )
    """)

    # Create indexes for faster queries
    index_statements = [
        "CREATE INDEX idx_works_title    ON works(title(255))",
        "CREATE INDEX idx_editions_group ON editions(group_id)",
    ]
    for sql in index_statements:
        try:
            cursor.execute(sql)
        except mysql.connector.errors.DatabaseError:
            pass  # index already exists
        
    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables and indexes created.")

if __name__ == '__main__':
    setup()