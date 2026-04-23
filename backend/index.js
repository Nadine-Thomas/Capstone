import express from "express";
import { createConnection } from "mysql2";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config({ path: "../.env" });

const app = express();
app.use(cors({ origin: "https://capstone-mofx.onrender.com" }));

const db = createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  port: process.env.DB_PORT || 3306,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  ssl: { rejectUnauthorized: false },
});

app.get("/api/books", (req, res) => {
  const { q } = req.query;
  if (!q) return res.status(400).json({ error: "Missing query" });

  const searchTerm = q.trim();

  db.query(
    `SELECT DISTINCT w.group_id, w.title 
     FROM works w
     INNER JOIN recommendations r ON w.group_id = r.group_id
     WHERE w.title LIKE ? 
     ORDER BY 
       // 1. Exact matches get top priority
       CASE WHEN w.title = ? THEN 0 
            // 2. Titles starting with the search term (e.g., "Jane Eyre (Deluxe)") */
            WHEN w.title LIKE ? THEN 1 
            // 3. Titles containing the search term elsewhere
            ELSE 2 
       END,
       // 4. Tie-breaker: Pick the shortest title (prevents picking long subtitles)
       LENGTH(w.title) ASC
     LIMIT 1`,
    [`%${searchTerm}%`, searchTerm, `${searchTerm}%`],
    (err, rows) => {
      if (err) return res.status(500).json({ error: "Database error" });

      // If no recommendations exist for any title matching "Jane Eyre", return empty
      if (rows.length === 0) return res.json([]);

      const groupId = rows[0].group_id;

      // Proceed to fetch the 5 recommendations for this specific group_id...
      db.query(
        `SELECT recommended_title, score
         FROM recommendations
         WHERE group_id = ?
         ORDER BY rec_rank ASC
         LIMIT 5`,
        [groupId],
        (err, recommendations) => {
          if (err) return res.status(500).json({ error: "Database error" });
          res.json(recommendations);
        },
      );
    },
  );
});

db.connect((err) => {
  if (err) {
    console.log("MySQL Connection Error:", err);
  } else {
    console.log("MySQL Connected!");
  }
});

app.listen(5000, () => {
  console.log("Server running on port 5000");
});
