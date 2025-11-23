-- Data for the 'music_store_db' dataset

INSERT INTO artists (id, name) VALUES
(1, 'The Beatles'),
(2, 'Pink Floyd'),
(3, 'Led Zeppelin');

INSERT INTO albums (id, title, artist_id) VALUES
(1, 'Abbey Road', 1),
(2, 'The Dark Side of the Moon', 2),
(3, 'Led Zeppelin IV', 3),
(4, 'The White Album', 1);

INSERT INTO tracks (id, track_name, album_id, duration_sec) VALUES
(1, 'Come Together', 1, 259),
(2, 'Something', 1, 182),
(3, 'Money', 2, 382),
(4, 'Us and Them', 2, 462),
(5, 'Black Dog', 3, 296),
(6, 'Stairway to Heaven', 3, 482),
(7, 'While My Guitar Gently Weeps', 4, 285);