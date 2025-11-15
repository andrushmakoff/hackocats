-- =====================
-- Структура базы Геркон 
-- =====================

-- Включаем PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- ENUM-типы
CREATE TYPE object_type AS ENUM (
    'node', 'muf', 'cabinet', 'splitter', 'abonent', 
    'cable', 'pole', 'camera', 'well', 'wifi'
);

CREATE TYPE fiber_status AS ENUM ('free', 'spliced', 'broken');

CREATE TYPE link_type AS ENUM ('cable_to_muf', 'muf_to_house', 'other');

-- Таблица объектов
CREATE TABLE objects (
    id SERIAL PRIMARY KEY,
    type object_type NOT NULL,
    name TEXT,
    description TEXT,
    location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_objects_location ON objects USING GIST(location);

-- Таблица параметров
CREATE TABLE object_properties (
    id SERIAL PRIMARY KEY,
    object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT
);

-- Таблица кабелей
CREATE TABLE cables (
    id SERIAL PRIMARY KEY,
    object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    fiber_count INT,
    length_meters FLOAT,
    start_object_id INT REFERENCES objects(id),
    end_object_id INT REFERENCES objects(id)
);

-- Геометрия кабеля
CREATE TABLE cable_geometry (
    id SERIAL PRIMARY KEY,
    cable_id INT REFERENCES cables(id) ON DELETE CASCADE,
    geom GEOGRAPHY(LINESTRING, 4326)
);
CREATE INDEX idx_cable_geometry ON cable_geometry USING GIST(geom);

-- Таблица волокон
CREATE TABLE fibers (
    id SERIAL PRIMARY KEY,
    cable_id INT REFERENCES cables(id) ON DELETE CASCADE,
    fiber_number INT,
    color TEXT,
    status fiber_status DEFAULT 'free'
);

-- Таблица сварок
CREATE TABLE splices (
    id SERIAL PRIMARY KEY,
    fiber_id INT REFERENCES fibers(id) ON DELETE CASCADE,
    splice_object_id INT REFERENCES objects(id),
    connected_fiber_id INT REFERENCES fibers(id)
);

-- Связи объектов
CREATE TABLE links (
    id SERIAL PRIMARY KEY,
    from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    to_object_id INT REFERENCES objects(id),
    type link_type
);

-- Пользователи и API-токены
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);

CREATE TABLE api_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP
);