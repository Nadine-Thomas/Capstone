import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from db import get_db_connection

def setup():
    # Connect to the database 
    conn   = get_db_connection()
    cursor = conn.cursor()

    # Create table books if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id VARCHAR(50) PRIMARY KEY,
            title VARCHAR(500),
            group_id VARCHAR(50),
            author_id VARCHAR(50)
        )
    ''')

    # Create table recommendations if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            group_id              VARCHAR(50),
            rec_rank              TINYINT,
            recommended_group_id  VARCHAR(50),
            recommended_title     VARCHAR(500),
            score                 FLOAT,
            PRIMARY KEY (group_id, rec_rank)
        )
    ''')

    # Create indexes for faster queries
    for index_sql in [
        "CREATE INDEX IF NOT EXISTS idx_group_id ON recommendations(group_id)",
        "CREATE INDEX IF NOT EXISTS idx_title on books(title(255))",
        "CREATE INDEX IF NOT EXISTS idx_group ON books(group_id)",
    ]:
        try:
            cursor.execute(index_sql)
        except mysql.connector.errors.DatabaseError:
            pass

    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables and indexes created.")

if __name__ == '__main__':
    setup()