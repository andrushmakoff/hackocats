-- PostgreSQL schema with PostGIS

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE object_type AS ENUM (
    'node', 'muf', 'cabinet', 'splitter',
    'abonent', 'cable', 'pole', 'camera',
    'well', 'wifi'
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE objects (
    id SERIAL PRIMARY KEY,
    type object_type NOT NULL,
    name TEXT,
    description TEXT,
    location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE object_properties (
    id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT
);

CREATE TABLE cables (
    id SERIAL PRIMARY KEY,
    object_id INTEGER UNIQUE REFERENCES objects(id) ON DELETE CASCADE,
    fiber_count INTEGER NOT NULL,
    length_meters INTEGER,
    start_object_id INTEGER REFERENCES objects(id),
    end_object_id INTEGER REFERENCES objects(id)
);

CREATE TABLE cable_geometry (
    id SERIAL PRIMARY KEY,
    cable_id INTEGER REFERENCES cables(id) ON DELETE CASCADE,
    geom GEOGRAPHY(LINESTRING, 4326) NOT NULL
);

CREATE TABLE fibers (
    id SERIAL PRIMARY KEY,
    cable_id INTEGER REFERENCES cables(id) ON DELETE CASCADE,
    fiber_number INTEGER NOT NULL,
    color TEXT,
    status TEXT DEFAULT 'free',
    UNIQUE (cable_id, fiber_number)
);

CREATE TABLE splices (
    id SERIAL PRIMARY KEY,
    fiber_id INTEGER REFERENCES fibers(id) ON DELETE CASCADE,
    splice_object_id INTEGER REFERENCES objects(id),
    connected_fiber_id INTEGER REFERENCES fibers(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE links (
    id SERIAL PRIMARY KEY,
    from_object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    to_object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_objects_type ON objects(type);
CREATE INDEX idx_objects_location ON objects USING GIST(location);
CREATE INDEX idx_cable_geom ON cable_geometry USING GIST(geom);
CREATE INDEX idx_fibers_cable ON fibers(cable_id);
CREATE INDEX idx_links_from ON links(from_object_id);
CREATE INDEX idx_links_to ON links(to_object_id);
