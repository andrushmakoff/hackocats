-- Этот файл будет выполнен автоматически при создании контейнера

-- Включаем PostGIS (в образе postgis/postgis он уже установлен)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Ваш оригинальный скрипт (я его чуть подправил — добавил IF NOT EXISTS где нужно, чтобы можно было перезапускать)
DO $$ BEGIN
    CREATE TYPE object_type AS ENUM (
        'node', 'muf', 'cabinet', 'splitter', 'abonent',
        'cable', 'pole', 'camera', 'well', 'wifi'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE fiber_status AS ENUM ('free', 'spliced', 'broken');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE link_type AS ENUM ('cable_to_muf', 'muf_to_house', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS objects (
    id SERIAL PRIMARY KEY,
    type object_type NOT NULL,
    name TEXT,
    description TEXT,
    location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_objects_location ON objects USING GIST(location);

CREATE TABLE IF NOT EXISTS object_properties (
    id SERIAL PRIMARY KEY,
    object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT
);

CREATE TABLE IF NOT EXISTS cables (
    id SERIAL PRIMARY KEY,
    object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    fiber_count INT,
    length_meters FLOAT,
    start_object_id INT REFERENCES objects(id),
    end_object_id INT REFERENCES objects(id)
);

CREATE TABLE IF NOT EXISTS cable_geometry (
    id SERIAL PRIMARY KEY,
    cable_id INT REFERENCES cables(id) ON DELETE CASCADE,
    geom GEOGRAPHY(LINESTRING, 4326)
);

CREATE INDEX IF NOT EXISTS idx_cable_geometry ON cable_geometry USING GIST(geom);

CREATE TABLE IF NOT EXISTS fibers (
    id SERIAL PRIMARY KEY,
    cable_id INT REFERENCES cables(id) ON DELETE CASCADE,
    fiber_number INT,
    color TEXT,
    status fiber_status DEFAULT 'free'
);

CREATE TABLE IF NOT EXISTS splices (
    id SERIAL PRIMARY KEY,
    fiber_id INT REFERENCES fibers(id) ON DELETE CASCADE,
    splice_object_id INT REFERENCES objects(id),
    connected_fiber_id INT REFERENCES fibers(id)
);

CREATE TABLE IF NOT EXISTS links (
    id SERIAL PRIMARY KEY,
    from_object_id INT REFERENCES objects(id) ON DELETE CASCADE,
    to_object_id INT REFERENCES objects(id),
    type link_type
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,                  -- Название региона
    center GEOGRAPHY(POINT, 4326),       -- Центр карты (куда зумить)
    zoom INT DEFAULT 13                  -- Начальный зум
);

CREATE TABLE IF NOT EXISTS map_tile_layers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    layer_type TEXT NOT NULL,
    url TEXT NOT NULL,
    attribution TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    min_zoom INT DEFAULT 0,
    max_zoom INT DEFAULT 19
);

CREATE TABLE IF NOT EXISTS splitters (
    id SERIAL PRIMARY KEY,
    object_id INT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    input_port_count INT DEFAULT 1,
    output_port_count INT NOT NULL,
    ratio TEXT NOT NULL,               -- '1:2', '1:4', '1:8', ...
    manufacturer TEXT,
    model TEXT,
    insertion_loss FLOAT               -- потери
);

CREATE TABLE IF NOT EXISTS splitter_ports (
    id SERIAL PRIMARY KEY,
    splitter_id INT NOT NULL REFERENCES splitters(id) ON DELETE CASCADE,
    port_number INT NOT NULL,
    port_type TEXT NOT NULL,           -- 'input' или 'output'
    connected_fiber_id INT REFERENCES fibers(id),
    UNIQUE(splitter_id, port_number)
);


INSERT INTO map_tile_layers (name, layer_type, url, attribution, is_default) VALUES
('OSM Standard', 'tile', 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
 E'© OpenStreetMap contributors', TRUE),
('OSM Humanitarian', 'tile', 'https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png',
 E'© OpenStreetMap contributors', FALSE),
('Google Satellite (proxy)', 'tile', 'https://your-proxy/google/sat/{z}/{x}/{y}.jpg',
 E'© Google LLC', FALSE),
('Yandex Satellite (proxy)', 'tile', 'https://your-proxy/yandex/sat/{z}/{x}/{y}.jpg',
 E'© Yandex LLC', FALSE),
('Корпоративная карта', 'tile', 'https://tiles.company.local/main/{z}/{x}/{y}.png',
 E'© Company GIS', FALSE);