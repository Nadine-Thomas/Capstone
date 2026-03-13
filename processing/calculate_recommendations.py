import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    BOOKS_OUTPUT_FILE,
    REVIEWS_OUTPUT_FILE,
    RECOMMENDATIONS_OUTPUT_FILE,
    TOP_K_BOOKS,
    TOP_K,
    CHUNK_SIZE,
    TFIDF_MAX_DF,
    TFIDF_MAX_FEATURES,
    TFIDF_NGRAM_RANGE,
)

# Weight reviews so that books people like influence recommendations more
def weight_review(rating, text):
    if rating == 5:
        return (text + " ") * 3
    if rating == 4:
        return (text + " ") * 2
    if rating in [1, 2, 3]:
        return text
    return ""


def build_book_corpus(reviews, book_id_to_group):
    """
    Combine all reviews for each book group into a single text document.

    Books can have multiple editions with different IDs. book_id_to_group maps 
    each edition's ID to a single group_id so all editions of the same work are 
    treated as one book.

    Each review is weighted by its star rating before aggregation.
    Returns a Series indexed by group_id where each value is the full review corpus
    for that group.
    """
    reviews = reviews.copy()
    # Reviews only contain book id, book editions need to be mapped to one group id
    reviews["group_id"] = reviews["book_id"].map(book_id_to_group)
    reviews = reviews.dropna(subset=["group_id"])

    reviews["weighted_review"] = reviews.apply(
        lambda row: weight_review(row["rating"], row["review_text"]), axis=1
    )

    return reviews.groupby("group_id")["weighted_review"].apply(
        lambda x: " ".join(r for r in x if len(r) > 0)
    )


def compute_recommendations(book_reviews, group_id_to_title, group_id_to_author, top_k, chunk_size):
    """
    Compute TF-IDF cosine similarity across all groups and return a DataFrame
    of the top_k recommendations per group.

    TF-IDF (Term Frequency–Inverse Document Frequency) turns each book's review
    corpus into a vector of word importance scores. Cosine similarity between two
    vectors then measures how similar the language used to describe two books is,
    regardless of document length.

    Computing the full N×N similarity matrix at once would require O(N²) memory.
    Instead the matrix is processed in row chunks of size chunk_size, computing only
    chunk_size rows of similarities at a time and discarding them after extracting
    the top-k results.

    Columns returned: group_id, rec_rank, recommended_group_id, recommended_title, score
    """
    tfidf = TfidfVectorizer(
        ngram_range = TFIDF_NGRAM_RANGE,
        max_df = TFIDF_MAX_DF,
        max_features = TFIDF_MAX_FEATURES,
    )
    tfidf_matrix = tfidf.fit_transform(book_reviews)

    group_ids = book_reviews.index.tolist()
    n = len(group_ids)
    results = []

    for i in range(0, n, chunk_size):
        # Only compute a section of similarities at a time
        chunk_matrix = tfidf_matrix[i:i + chunk_size]
        sim_chunk = cosine_similarity(chunk_matrix, tfidf_matrix)

        # A book is always perfectly similar to itself (score = 1.0).
        # Zero that out so it can never appear as its own recommendation.
        for row_in_chunk in range(sim_chunk.shape[0]):
            book_idx = i + row_in_chunk
            sim_chunk[row_in_chunk, book_idx] = 0

        for row_in_chunk, similarity in enumerate(sim_chunk):
            group_idx = i + row_in_chunk
            group_id = group_ids[group_idx]
            own_author = group_id_to_author.get(group_id)

            # Rearranges the array so that the top_k largest values end up in 
            # the last top_k positions, but those positions are not sorted 
            top_indices = np.argpartition(similarity, -top_k)[-top_k:]
            # Sort just those top_k candidates from highest to lowest score
            top_indices = top_indices[np.argsort(similarity[top_indices])[::-1]]

            rank = 1
            for rec_idx in top_indices:
                if rank > top_k:
                    break
                rec_group_id = group_ids[int(rec_idx)]
                rec_author = group_id_to_author.get(rec_group_id)
                # Skip recommendations from the same author to ensure diversity
                if own_author and rec_author and own_author == rec_author:
                    continue
                rec_title = group_id_to_title.get(rec_group_id, "Unknown")
                score = round(float(similarity[rec_idx]), 4)
                results.append((group_id, rank, rec_group_id, rec_title, score))
                rank += 1


    return pd.DataFrame(
        results,
        columns=["group_id", "rec_rank", "recommended_group_id", "recommended_title", "score"],
    )


def run(books_file, reviews_file, output_file):
    print("Loading data...")
    reviews = pd.read_json(reviews_file, lines=True)
    books = pd.read_json(books_file, lines=True)

    # Assign a unique group_id for each work
    books["group_id"] = books.index.astype(str)

    # Separate grouped book ids to map later
    books_exploded = books.explode("book_ids").rename(columns={"book_ids": "book_id"}) 
    # Ensure that book id from books and reviews are the same type to map later
    books_exploded["book_id"] = books_exploded["book_id"].astype(str)
    reviews["book_id"] = reviews["book_id"].astype(str)

    # Create dictionaries for efficiency 
    book_id_to_group = books_exploded.set_index("book_id")["group_id"].to_dict()
    group_id_to_title = books.set_index("group_id")["title"].to_dict()
    group_id_to_author = books.set_index("group_id")["author_id"].to_dict()

    # Restrict to the top N most-reviewed book_ids to keep computation tractable
    top_book_ids = (
        reviews.groupby("book_id")["review_text"]
        .count()
        .nlargest(TOP_K_BOOKS)
        .index
    )
    reviews = reviews[reviews["book_id"].isin(top_book_ids)]

    print("Building per-group review corpus...")
    book_reviews = build_book_corpus(reviews, book_id_to_group)

    print(f"Computing recommendations...")
    df = compute_recommendations(book_reviews, group_id_to_title, group_id_to_author, TOP_K, CHUNK_SIZE)

    df.to_csv(output_file, index=False)
    print(f"Saved {len(df):,} recommendation rows to: {output_file}")


if __name__ == "__main__":
    run(BOOKS_OUTPUT_FILE, REVIEWS_OUTPUT_FILE, RECOMMENDATIONS_OUTPUT_FILE,)