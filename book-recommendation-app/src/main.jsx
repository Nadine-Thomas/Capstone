/**
 * main.jsx — Application entry point.
 *
 * Mounts the React app into the #root DOM element and defines the two
 * top-level routes:
 *   / for App  (home / search input)
 *   /search for Search (results page, expects ?q= query param)
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import SearchPage from "./Search.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
