// server.js
const express = require("express");
const { Pool } = require("pg");
const path = require("path");
const bodyParser = require("body-parser");

const app = express();
const PORT = 8000;

// ========= MIDDLEWARE =========
app.use(bodyParser.json());
app.use("/static", express.static(path.join(__dirname, "static")));

// ========= POSTGRES =========
const pool = new Pool({
  host: "localhost",
  user: "postgres",
  password: "sqlbase7comiloveu",
  database: "gerkon_db",
  port: 5432,
});

// ========= ИНИЦИАЛИЗАЦИЯ БАЗЫ =========
async function initDB() {
  const client = await pool.connect();
  try {
    // Таблица объектов (точек)
    await client.query(`
      CREATE TABLE IF NOT EXISTS objects (
        id SERIAL PRIMARY KEY,
        type VARCHAR(50) NOT NULL,
        name VARCHAR(255),
        description TEXT,
        location GEOGRAPHY(POINT,4326),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );
    `);

    // Таблица линий
    await client.query(`
      CREATE TABLE IF NOT EXISTS lines (
        id SERIAL PRIMARY KEY,
        from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
        to_object_id INT REFERENCES objects(id) ON DELETE CASCADE
      );
    `);
  } finally {
    client.release();
  }
}

initDB().catch(console.error);

// ========= ROUTES =========

// Статическая главная страница
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "static", "index.html"));
});

// -------- POINTS --------

// GET all points
app.get("/api/points", async (req, res) => {
  const client = await pool.connect();
  try {
    const result = await client.query(`
      SELECT id, type, name, description,
             ST_Y(location::geometry) AS lat,
             ST_X(location::geometry) AS lon
      FROM objects;
    `);
    res.json(result.rows);
  } finally {
    client.release();
  }
});

// POST create point
app.post("/api/points", async (req, res) => {
  const { type, name, description, lat, lon } = req.body;
  const client = await pool.connect();
  try {
    const result = await client.query(
      `INSERT INTO objects (type,name,description,location)
       VALUES ($1,$2,$3,ST_SetSRID(ST_MakePoint($4,$5),4326))
       RETURNING *;`,
      [type, name, description, lon, lat]
    );
    res.json(result.rows[0]);
  } finally {
    client.release();
  }
});

// PATCH update point
app.patch("/api/points/:id", async (req, res) => {
  const { id } = req.params;
  const { name, description } = req.body;
  const client = await pool.connect();
  try {
    const result = await client.query(
      `UPDATE objects SET name=$1, description=$2, updated_at=NOW() WHERE id=$3 RETURNING *;`,
      [name, description, id]
    );
    if (result.rows.length === 0) {
      res.status(404).json({ error: "Point not found" });
    } else {
      res.json({ status: "ok" });
    }
  } finally {
    client.release();
  }
});

// DELETE point
app.delete("/api/points/:id", async (req, res) => {
  const { id } = req.params;
  const client = await pool.connect();
  try {
    const result = await client.query(`DELETE FROM objects WHERE id=$1 RETURNING *;`, [id]);
    if (result.rows.length === 0) {
      res.status(404).json({ error: "Point not found" });
    } else {
      res.json({ status: "deleted", id: Number(id) });
    }
  } finally {
    client.release();
  }
});

// -------- LINES --------

// GET all lines
app.get("/api/lines", async (req, res) => {
  const client = await pool.connect();
  try {
    const result = await client.query("SELECT id, from_object_id, to_object_id FROM lines;");
    res.json(result.rows);
  } finally {
    client.release();
  }
});

// POST create line
app.post("/api/lines", async (req, res) => {
  const { a, b } = req.body;
  const client = await pool.connect();
  try {
    const result = await client.query(
      `INSERT INTO lines (from_object_id, to_object_id) VALUES ($1,$2) RETURNING *;`,
      [a, b]
    );
    res.json(result.rows[0]);
  } finally {
    client.release();
  }
});

// ========= SERVER =========
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
