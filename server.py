import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psycopg2
from psycopg2.extras import RealDictCursor

# ========= БАЗА ДАННЫХ =========

DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "sqlbase7comiloveu",
    "database": "gerkon_db",
    "port": 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица объектов (точек)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objects (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            name VARCHAR(255),
            description TEXT,
            location GEOGRAPHY(POINT,4326),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Таблица линий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lines (
            id SERIAL PRIMARY KEY,
            from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
            to_object_id INT REFERENCES objects(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# Инициализация базы
init_db()

# ========= FASTAPI =========

app = FastAPI(title="Map REST API")

# ========= СТАТИКА =========

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

# ========= МОДЕЛИ =========

class PointCreate(BaseModel):
    type: str
    name: Optional[str] = None
    description: Optional[str] = None
    lat: float
    lon: float

class PointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class LineCreate(BaseModel):
    a: int
    b: int

# ========= ROUTES POINTS =========

@app.get("/api/points", response_model=List[dict])
def get_points():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, type, name, description,
               ST_Y(location::geometry) AS lat,
               ST_X(location::geometry) AS lon
        FROM objects;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/points", response_model=dict)
def create_point(data: PointCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO objects (type, name, description, location)
        VALUES (%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326))
        RETURNING id;
    """, (data.type, data.name, data.description, data.lon, data.lat))
    new_id = cursor.fetchone()["id"]
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": new_id, "type": data.type, "name": data.name, "description": data.description, "lat": data.lat, "lon": data.lon}

@app.patch("/api/points/{point_id}", response_model=dict)
def update_point(point_id: int, data: PointUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM objects WHERE id=%s;", (point_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Point not found")
    cursor.execute("""
        UPDATE objects
        SET name=%s, description=%s, updated_at=NOW()
        WHERE id=%s;
    """, (data.name, data.description, point_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status":"ok"}

@app.delete("/api/points/{point_id}", response_model=dict)
def delete_point(point_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM objects WHERE id=%s RETURNING id;", (point_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Point not found")
    conn.commit()
    cursor.close()
    conn.close()
    return {"status":"deleted", "id": point_id}

# ========= ROUTES LINES =========

@app.get("/api/lines", response_model=List[dict])
def get_lines():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, from_object_id, to_object_id FROM lines;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/lines", response_model=dict)
def create_line(data: LineCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lines (from_object_id, to_object_id)
        VALUES (%s,%s) RETURNING id;
    """, (data.a, data.b))
    new_id = cursor.fetchone()["id"]
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": new_id, "a": data.a, "b": data.b}
