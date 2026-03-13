/**
 * Search.jsx — Results page of the Book Recommendation App.
 *
 * Reads the search query from the URL (?q=...), fetches book recommendations
 * from the backend API, and displays them as an animated ordered list.
 * Handles loading, error, and empty-results states.
 */

import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

function Search() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const query = params.get("q");

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = "Recommendations";
  }, []);

  // Fetch recommendations whenever the query changes
  useEffect(() => {
    if (!query) return;
    setLoading(true);
    fetch(
      `https://book-recommendation-app-acbu.onrender.com/api/books?q=${encodeURIComponent(query)}`,
    )
      .then((res) => res.json())
      .then((data) => {
        setRecommendations(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to fetch recommendations");
        setLoading(false);
      });
  }, [query]);

  return (
    <div className="app">
      <div className="container results-container">
        <button onClick={() => navigate(-1)} className="back-btn">
          ← Back
        </button>

        <div className="heading">
          <p className="search-label">Recommendations for</p>
          <h1 className="title">
            {/* Display the entered book title capitalized */}"
            {query?.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}"
          </h1>
        </div>

        <div className="divider">
          <div className="divider-line-left" />
          ✦ ✧ ✦
          <div className="divider-line-right" />
        </div>

        {/* Loading state */}
        {loading && (
          <div className="results-status">
            <span className="status-dot loading-dot" />
            Loading recommendations...
          </div>
        )}

        {/* Error state */}
        {error && <div className="results-status error-text">{error}</div>}

        {/* Empty state */}
        {!loading && !error && recommendations.length === 0 && (
          <div className="results-status">No recommendations found.</div>
        )}

        {/* Results list, each card fades in with a staggered delay */}
        {!loading && recommendations.length > 0 && (
          <ol className="results-list">
            {recommendations.map((rec, i) => (
              <li
                key={i}
                className="result-card"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <span className="result-number">{String(i + 1)}</span>
                <div className="result-info">
                  <span className="result-title">
                    {rec.recommended_title
                      ?.toLowerCase()
                      .replace(/\b\w/g, (char) => char.toUpperCase())}
                  </span>
                  {rec.score != null && (
                    <span className="result-score">
                      {(rec.score * 100).toFixed(0)}% match
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

export default Search;
