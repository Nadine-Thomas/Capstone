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

  if (!q) {
    return res.status(400).json({ error: "Missing query parameter" });
  }

  // Step 1: Find the book
  db.query(
    "SELECT group_id FROM books WHERE title LIKE ? LIMIT 1",
    [`%${q}%`],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });

      if (rows.length === 0) {
        return res.json([]);
      }

      const groupId = rows[0].group_id;

      // Step 2: Get recommendations
      db.query(
        `SELECT recommended_title, score
         FROM recommendations
         WHERE group_id = ?
         ORDER BY rec_rank ASC
         LIMIT 5`,
        [groupId],
        (err, recommendations) => {
          if (err) return res.status(500).json({ error: err.message });

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
