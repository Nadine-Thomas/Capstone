import pandas as pd
import numpy as np
import csv
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.pipeline import Pipeline
import faiss

from config import (
    BOOKS_OUTPUT_FILE,
    REVIEWS_OUTPUT_FILE,
    RECOMMENDATIONS_OUTPUT_FILE,
    TOP_K_BOOKS,
    TOP_K,
    CHUNK_SIZE,
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


def compute_recommendations(book_reviews, group_id_to_title, group_id_to_author, top_k, chunk_size, output_file):
    """
    Build a TF-IDF + SVD embedding for each book group, then use FAISS to find
    the top_k most similar books per group based on cosine similarity.

    Pipeline:
      1. HashingVectorizer — converts review text to sparse term-frequency
         vectors using hashing, avoiding a full vocabulary-building pass.
      2. TfidfTransformer — applies IDF weighting and sublinear TF scaling so
         common words are down-weighted and rare descriptive words matter more.
      3. TruncatedSVD — reduces the high-dimensional sparse matrix to a dense
         lower-dimensional embedding, capturing latent semantic structure.
      4. L2 normalisation — puts all vectors on the unit sphere so that inner
         product equals cosine similarity.
      5. FAISS IndexFlatIP — exact inner-product (cosine) nearest-neighbour
         search over the normalised vectors.

    To avoid creating the full N×N similarity matrix, the FAISS search is 
    performed in row chunks of size chunk_size. Only top_k results per row are 
    kept before moving to the next chunk.

    Columns written to output_file (CSV):
        group_id, rec_rank, recommended_group_id, recommended_title, score
    """

    print("Fitting TF-IDF...")
    pipe = Pipeline([
        ("hash", HashingVectorizer(
            ngram_range=(1, 3),
            n_features=2**20,  # ~1M hash buckets; reduces collision risk without a vocab pass
            norm=None,
            alternate_sign=False,
            dtype=np.float32,
        )),
        ("tfidf", TfidfTransformer(sublinear_tf=True)),
    ])

    tfidf_matrix = pipe.fit_transform(book_reviews)

    print(f"Reducing dimensions with SVD ({512} components)...")
    svd = TruncatedSVD(n_components=512, random_state=42)
    # Reduce to 512 latent dimensions; captures semantic similarity while
    # keeping the FAISS index small and search fast
    vectors = svd.fit_transform(tfidf_matrix).astype(np.float32)  # shape: (n_books, 512)

    explained = svd.explained_variance_ratio_.sum()
    print(f"SVD explains {explained:.1%} of variance")

    print("Normalizing vectors...")
    # L2-normalise so cosine similarity == inner product (required by IndexFlatIP)
    vectors = normalize(vectors, norm="l2").astype(np.float32)

    group_ids = book_reviews.index.tolist()
    n = len(group_ids)
    # Vector dimension after SVD
    dim = vectors.shape[1]

     # Build an exact inner-product index
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    # Sanity-check: after L2 normalisation every vector should have unit norm
    vectors = normalize(vectors, norm="l2").astype(np.float32)
    print("Norm check:", np.linalg.norm(vectors[0])) 

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["group_id", "rec_rank", "recommended_group_id", "recommended_title", "score"])

        for i in range(0, n, chunk_size):
            results = []
            chunk = vectors[i:i + chunk_size]

            # Request top_k + 1 because each book will match itself with score 1.0
            scores, indices = index.search(chunk, top_k + 1)

            for row_in_chunk in range(chunk.shape[0]):
                group_idx = i + row_in_chunk
                group_id = group_ids[group_idx]
                own_author = group_id_to_author.get(group_id)

                rank = 1
                for rec_idx, score in zip(indices[row_in_chunk], scores[row_in_chunk]):
                    if rank > top_k:
                        break          
                    # Skip the book itself (always returned as the top match)
                    if rec_idx == group_idx:
                        continue
                    rec_group_id = group_ids[int(rec_idx)]
                    rec_author = group_id_to_author.get(rec_group_id)
                    # Skip recommendations from the same author to ensure diversity
                    if own_author and rec_author and own_author == rec_author:
                        continue
                    rec_title = group_id_to_title.get(rec_group_id, "Unknown")
                    results.append((group_id, rank, rec_group_id, rec_title, round(float(score), 4)))
                    rank += 1

            writer.writerows(results)
            print(f"Processed {min(i + chunk_size, n)}/{n}")

    return pd.read_csv(output_file)


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

    print("Computing recommendations...")
    df = compute_recommendations(book_reviews, group_id_to_title, group_id_to_author, TOP_K, CHUNK_SIZE, output_file)

    df.to_csv(output_file, index=False)
    print(f"Saved {len(df):,} recommendation rows to: {output_file}")


if __name__ == "__main__":
    run(BOOKS_OUTPUT_FILE, REVIEWS_OUTPUT_FILE, RECOMMENDATIONS_OUTPUT_FILE)