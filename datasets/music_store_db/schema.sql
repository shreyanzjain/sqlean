-- Schema for the 'music_store_db' dataset

CREATE TABLE artists (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE albums (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
);

CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    album_id INTEGER,
    duration_sec INTEGER,
    FOREIGN KEY (album_id) REFERENCES albums(id)
);