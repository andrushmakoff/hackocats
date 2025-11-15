from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, String, Table, MetaData, insert, select
import os

# --- Настройка сервера ---
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Подключение к SQLite ---
db_path = os.path.join(BASE_DIR, "map.db")
db = create_engine(f"sqlite:///{db_path}", echo=False)
meta = MetaData()

# --- Таблицы ---
points = Table(
    "points", meta,
    Column("id", Integer, primary_key=True),
    Column("lat", Float),
    Column("lon", Float),
    Column("type", String)
)

lines = Table(
    "lines", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("a", Integer),
    Column("b", Integer)
)

meta.create_all(db)

# --- Модели ---
class Point(BaseModel):
    id: int
    lat: float
    lon: float
    type: str

class Line(BaseModel):
    a: int
    b: int

# --- API ---
@app.get("/api/get_all")
def get_all():
    with db.connect() as conn:
        pts = conn.execute(select(points)).fetchall()
        lns = conn.execute(select(lines)).fetchall()
        return {
            "points": [{"id": p.id, "lat": p.lat, "lon": p.lon, "type": p.type} for p in pts],
            "lines": [{"a": l.a, "b": l.b} for l in lns]
        }

@app.post("/api/add_point")
def add_point(pt: Point):
    with db.connect() as conn:
        conn.execute(insert(points).values(id=pt.id, lat=pt.lat, lon=pt.lon, type=pt.type))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/update_point")
def update_point(pt: Point):
    with db.connect() as conn:
        result = conn.execute(
            points.update().where(points.c.id == pt.id).values(lat=pt.lat, lon=pt.lon)
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Point not found")
    return {"status": "ok"}

@app.post("/api/delete_point")
def delete_point(pt: Point):
    with db.connect() as conn:
        # удаляем линии с этой точкой
        conn.execute(lines.delete().where((lines.c.a == pt.id) | (lines.c.b == pt.id)))
        # удаляем саму точку
        result = conn.execute(points.delete().where(points.c.id == pt.id))
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Point not found")
    return {"status": "ok"}

@app.post("/api/add_line")
def add_line(line: Line):
    with db.connect() as conn:
        conn.execute(insert(lines).values(a=line.a, b=line.b))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/delete_line")
def delete_line(line: Line):
    with db.connect() as conn:
        result = conn.execute(
            lines.delete().where((lines.c.a == line.a) & (lines.c.b == line.b))
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Line not found")
    return {"status": "ok"}

# --- Статика (index.html и PNG-иконки) ---
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
