CREATE TABLE IF NOT EXISTS analysis (
    id SERIAL PRIMARY KEY,

    uid TEXT,

    image_path TEXT,

    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    location TEXT,

    latitude REAL,

    longitude REAL,

    is_anon BOOLEAN NOT NULL DEFAULT FALSE,

    status TEXT NOT NULL DEFAULT 'completed'
);


CREATE TABLE IF NOT EXISTS clouds (
    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE NOT NULL,

    forecast TEXT,

    warning TEXT,

    warning_level INTEGER
);

CREATE TABLE IF NOT EXISTS analysis_cloud (
    id SERIAL PRIMARY KEY,

    analysis_id INTEGER REFERENCES analysis(id) ON DELETE CASCADE,

    cloud_id INTEGER REFERENCES clouds(id),

    confidence FLOAT,

    box_ymin REAL,

    box_xmin REAL,

    box_ymax REAL,

    box_xmax REAL
);