from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, Table, MetaData, insert, select
from fastapi import FastAPI, HTTPException


# --- Настройка сервера ---
app = FastAPI()

# --- CORS (разрешаем любые запросы для фронтенда) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Подключение к SQLite ---
db = create_engine("sqlite:///map.db")
meta = MetaData()

points = Table(
    "points", meta,
    Column("id", Integer, primary_key=True),
    Column("x", Float),
    Column("y", Float),
)

lines = Table(
    "lines", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("a", Integer),
    Column("b", Integer),
)

meta.create_all(db)

# --- Модели данных для API ---
class Point(BaseModel):
    id: int
    x: float
    y: float

class Line(BaseModel):
    a: int
    b: int

# --- API ---
@app.get("/api/getPoints")
def get_points():
    with db.connect() as conn:
        pts = conn.execute(select(points)).fetchall()
        lns = conn.execute(select(lines)).fetchall()
        return {
            "points": [{"id": p.id, "x": p.x, "y": p.y} for p in pts],
            "lines": [{"a": l.a, "b": l.b} for l in lns]
        }

@app.post("/api/addPoint")
def add_point(pt: Point):
    with db.connect() as conn:
        conn.execute(insert(points).values(id=pt.id, x=pt.x, y=pt.y))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/addLine")
def add_line(line: Line):
    with db.connect() as conn:
        conn.execute(insert(lines).values(a=line.a, b=line.b))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/updatePoint")
def update_point(pt: Point):
    with db.connect() as conn:
        conn.execute(
            points.update().where(points.c.id == pt.id).values(x=pt.x, y=pt.y)
        )
        conn.commit()
    return {"status": "ok"}

@app.post("/api/deletePoint")
def delete_point(pt: Point):
    with db.connect() as conn:
        # Удаляем линии, где участвует эта точка
        conn.execute(lines.delete().where((lines.c.a == pt.id) | (lines.c.b == pt.id)))
        # Удаляем саму точку
        result = conn.execute(points.delete().where(points.c.id == pt.id))
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Point not found")
    return {"status": "ok"}

@app.post("/api/deleteLine")
def delete_line(line: Line):
    with db.connect() as conn:
        result = conn.execute(
            lines.delete().where((lines.c.a == line.a) & (lines.c.b == line.b))
        )
        conn.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Line not found")
    return {"status": "ok"}

# --- Статика ---
app.mount("/", StaticFiles(directory=".", html=True), name="static")
