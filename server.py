# server.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DB configs
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gerkon_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "sqlbase7comiloveu")
DB_PORT = int(os.getenv("DB_PORT", 5432))

app = FastAPI(title="Map API")

# static
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

# БАЗОВЫЕ МОДЕЛИ ---------------------

class PointCreate(BaseModel):
    type: str
    name: str | None = None
    description: str | None = None
    lat: float
    lon: float

class PointUpdate(BaseModel):
    id: int
    name: str | None
    description: str | None

class PointDelete(BaseModel):
    id: int

class LineCreate(BaseModel):
    a: int
    b: int

# DB CONNECTION -----------------------

conn = None
cursor = None

@app.on_event("startup")
def startup():
    global conn, cursor
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected to Postgres:", DB_HOST)
    except Exception as e:
        print("Failed to connect to Postgres:", e)
        raise


@app.on_event("shutdown")
def shutdown():
    global conn, cursor
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception:
        pass

# API ------------------------------------

@app.post("/api/add_point")
def add_point(point: PointCreate):

    query = """
        INSERT INTO objects (type, name, description, location)
        VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        RETURNING id
    """
    try:
        cursor.execute(query, (point.type, point.name, point.description, point.lon, point.lat))
        conn.commit()
        new = cursor.fetchone()
        return {"status": "ok", "id": new["id"]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get_all")
def get_all():
    query = """
        SELECT
            id,
            type,
            name,
            description,
            ST_Y(location::geometry) AS lat,
            ST_X(location::geometry) AS lon,
            created_at,
            updated_at
        FROM objects
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return {"points": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update_point")
def update_point(data: PointUpdate):
    query = """
        UPDATE objects
        SET name = %s,
            description = %s,
            updated_at = NOW()
        WHERE id = %s
    """
    try:
        cursor.execute(query, (data.name, data.description, data.id))
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/delete_point")
def delete_point(data: PointDelete):
    query = "DELETE FROM objects WHERE id = %s"
    try:
        cursor.execute(query, (data.id,))
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ------------------- Линии ----------------------

# Добавляем таблицу lines (если её нет)
@app.on_event("startup")
def create_lines_table():
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                id SERIAL PRIMARY KEY,
                from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
                to_object_id INT REFERENCES objects(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Failed to create lines table:", e)

@app.post("/api/add_line")
def add_line(line: LineCreate):
    query = """
        INSERT INTO lines (from_object_id, to_object_id)
        VALUES (%s, %s)
        RETURNING id
    """
    try:
        cursor.execute(query, (line.a, line.b))
        conn.commit()
        new = cursor.fetchone()
        return {"status": "ok", "id": new["id"]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_lines")
def get_lines():
    query = "SELECT id, from_object_id, to_object_id FROM lines"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return {"lines": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
