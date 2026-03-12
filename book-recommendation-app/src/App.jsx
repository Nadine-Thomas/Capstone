import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = () => {
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  };

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
            <span className="search-icon">⌕</span>
            <input
              className="search-input"
              type="text"
              placeholder="The Giver, Jane Eyre, etc."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
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
