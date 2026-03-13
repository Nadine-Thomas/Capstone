/**
 * App.jsx — Home page of the Book Recommendation App.
 *
 * Renders the landing page with a search input. On submit, navigates to
 * the /search route with the query encoded as a URL parameter (?q=...).
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  // Navigate to the search results page, ignoring blank input
  const handleSearch = () => {
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  };

  // Allow submitting the search with the enter key
  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="app">
      <header className="app-header">
        <title>Book Recommendation App</title>
      </header>
      <div className="container">
        <div className="heading">
          <h1 className="title"> Book Recommendation App </h1>
          <p className="subtitle">Find your next great read!</p>
        </div>

        <div className="divider">
          <div className="divider-line-left" />
          ✦ ✧ ✦
          <div className="divider-line-right" />
        </div>

        <section className="search-section">
          <label className="search-label">
            Enter a book title and find similar books
          </label>
          <div className="search-bar">
            <div className="search-input-row">
              <span className="search-icon">⌕</span>
              <input
                className="search-input"
                type="text"
                placeholder="The Hunger Games, Jane Eyre, etc."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>
            <button className="search-btn" onClick={handleSearch}>
              Search
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
