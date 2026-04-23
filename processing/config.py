""" Configuration file for the project.

This file contains all the configuration settings for the project, including 
necessary files and running specifications.
"""

# File paths
BOOKS_INPUT_FILE = "goodreads_books.json.gz"
BOOKS_OUTPUT_FILE = "goodreads_books_cleaned.json.gz"

REVIEWS_INPUT_FILE = "goodreads_reviews_dedup.json.gz"
REVIEWS_OUTPUT_FILE = "goodreads_reviews_cleaned.json.gz"

RECOMMENDATIONS_OUTPUT_FILE = "recommendations.csv"

# Upload settings
BATCH_SIZE = 10_000

# Recommendation settings
TOP_K_BOOKS = 10_000
TOP_K = 20
CHUNK_SIZE = 1_000
TFIDF_MAX_FEATURES = 100_000
TFIDF_MAX_DF = 0.80
TFIDF_NGRAM_RANGE = (1, 3)
