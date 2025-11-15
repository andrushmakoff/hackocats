# server.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# берём хост БД из переменных окружения (если не задано — localhost)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gerkon_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "sqlbase7comiloveu")
DB_PORT = int(os.getenv("DB_PORT", 5432))

app = FastAPI(title="Map API")

# монтируем статические файлы (папка ./static)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

# Pydantic модель
class PointCreate(BaseModel):
    type: str
    name: str | None = None
    description: str | None = None
    lat: float
    lon: float

# глобальные переменные для соединения/курсора
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
            host=DB_HOST,    # <- здесь используется переменная, а не строка "DB_HOST"
            port=DB_PORT
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected to Postgres:", DB_HOST)
    except Exception as e:
        # печатаем ошибку, чтобы видел при запуске
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
        rows = cursor.fetchall()  # список dict
        return {"points": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
