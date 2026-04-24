import express from "express";
import { createPool } from "mysql2";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config({ path: "../.env" });

const app = express();

const allowedOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(",")
  : ["http://localhost:5173", "https://capstone-mofx.onrender.com"];

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("Not allowed by CORS"));
      }
    },
  }),
);

const pool = createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  port: process.env.DB_PORT || 3306,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  ssl: { rejectUnauthorized: false },
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

pool.getConnection((err, connection) => {
  if (err) {
    console.error("MySQL connection failed:", err);
    process.exit(1);
  }
  console.log("MySQL connected!");
  connection.release();
});

app.get("/api/books", (req, res) => {
  const { q } = req.query;
  if (!q) return res.status(400).json({ error: "Missing query" });

  const searchTerm = q.trim();

  pool.query(
    `SELECT DISTINCT w.group_id, w.title
     FROM works w
     INNER JOIN recommendations r ON w.group_id = r.group_id
     WHERE w.title LIKE ?
     ORDER BY
       CASE
         WHEN w.title = ?        THEN 0
         WHEN w.title LIKE ?     THEN 1
         ELSE                         2
       END,
       LENGTH(w.title) ASC
     LIMIT 1`,
    [`%${searchTerm}%`, searchTerm, `${searchTerm}%`],
    (err, rows) => {
      if (err) {
        console.error("DB error (title lookup):", err);
        return res.status(500).json({ error: "Database error" });
      }

      if (rows.length === 0) return res.json([]);

      const groupId = rows[0].group_id;

      pool.query(
        `SELECT recommended_title, score
         FROM recommendations
         WHERE group_id = ?
         ORDER BY rec_rank ASC
         LIMIT 5`,
        [groupId],
        (err, recommendations) => {
          if (err) {
            console.error("DB error (recommendations):", err);
            return res.status(500).json({ error: "Database error" });
          }
          res.json(recommendations);
        },
      );
    },
  );
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
