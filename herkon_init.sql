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