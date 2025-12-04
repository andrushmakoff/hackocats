import express from "express";
import path from "path";
import dotenv from "dotenv";
import { fileURLToPath } from "url";
import pkg from "pg";

dotenv.config();
const { Pool } = pkg;

// ---------------------------
// Base DIR fix for ES Modules
// ---------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------
// Express Init
// ---------------------------
const app = express();
app.use(express.json());

// ---------------------------
// Static Directory
// ---------------------------
app.use("/static", express.static(path.join(__dirname, "static")));

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "static", "index.html"));
});

// ---------------------------
// PostgreSQL (Pool)
// ---------------------------
const pool = new Pool({
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    port: process.env.DB_PORT
});

// ------------------------------
// Create lines table on startup
// ------------------------------
async function initDatabase() {
    try {
        await pool.query(`
            CREATE TABLE IF NOT EXISTS lines (
                id SERIAL PRIMARY KEY,
                from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
                to_object_id INT REFERENCES objects(id) ON DELETE CASCADE
            );
        `);
        console.log("Table 'lines' checked/created.");
    } catch (err) {
        console.error("DB init error:", err);
    }
}

initDatabase();

// =========================================
// ===============   API   =================
// =========================================

// CREATE POINT ----------------------------
app.post("/api/add_point", async (req, res) => {
    const { type, name, description, lat, lon } = req.body;

    try {
        const query = `
            INSERT INTO objects (type, name, description, location)
            VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
            RETURNING id
        `;
        const result = await pool.query(query, [type, name, description, lon, lat]);
        res.json({ status: "ok", id: result.rows[0].id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET ALL POINTS --------------------------
app.get("/api/get_all", async (req, res) => {
    try {
        const query = `
            SELECT
                id,
                type,
                name,
                description,
                ST_Y(location::geometry) AS lat,
                ST_X(location::geometry) AS lon,
                created_at,
                updated_at
            FROM objects;
        `;
        const result = await pool.query(query);
        res.json({ points: result.rows });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// UPDATE POINT ----------------------------
app.post("/api/update_point", async (req, res) => {
    const { id, name, description } = req.body;

    try {
        const query = `
            UPDATE objects
            SET name = $1,
                description = $2,
                updated_at = NOW()
            WHERE id = $3
        `;
        await pool.query(query, [name, description, id]);
        res.json({ status: "ok" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// DELETE POINT ----------------------------
app.post("/api/delete_point", async (req, res) => {
    const { id } = req.body;

    try {
        await pool.query(`DELETE FROM objects WHERE id = $1`, [id]);
        res.json({ status: "ok" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// =========================================
// ===============  LINES  =================
// =========================================

// ADD LINE --------------------------------
app.post("/api/add_line", async (req, res) => {
    const { a, b } = req.body;

    try {
        const query = `
            INSERT INTO lines (from_object_id, to_object_id)
            VALUES ($1, $2)
            RETURNING id
        `;
        const result = await pool.query(query, [a, b]);
        res.json({ status: "ok", id: result.rows[0].id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// GET LINES -------------------------------
app.get("/api/get_lines", async (req, res) => {
    try {
        const result = await pool.query("SELECT id, from_object_id, to_object_id FROM lines");
        res.json({ lines: result.rows });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// =========================================
// =============== SERVER ==================
// =========================================
const PORT = 3000;
app.listen(PORT, () => console.log("Server running on http://localhost:" + PORT));
