import sqlite3

DB_FILE = "trakt_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create table for shows
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            season INTEGER,
            episode INTEGER,
            watched_at TEXT,
            trakt_id INTEGER UNIQUE
        )
    ''')

    # Create table for movies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            year INTEGER,
            watched_at TEXT,
            trakt_id INTEGER UNIQUE
        )
    ''')

    conn.commit()
    conn.close()

def save_history_to_db(username, shows, movies):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Save shows
    for entry in shows:
        show = entry.get("show", {})
        episode = entry.get("episode", {})
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO shows (username, title, season, episode, watched_at, trakt_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                username,
                show.get("title"),
                episode.get("season"),
                episode.get("number"),
                entry.get("watched_at"),
                entry.get("id")
            ))
        except Exception as e:
            print(f"Error saving show: {e}")

    # Save movies
    for entry in movies:
        movie = entry.get("movie", {})
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO movies (username, title, year, watched_at, trakt_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                username,
                movie.get("title"),
                movie.get("year"),
                entry.get("watched_at"),
                entry.get("id")
            ))
        except Exception as e:
            print(f"Error saving movie: {e}")

    conn.commit()
    conn.close()

def count_total_scrobbles(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM movies WHERE username = ?", (username,))
    movie_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM shows WHERE username = ?", (username,))
    show_count = cursor.fetchone()[0]

    conn.close()
    return movie_count, show_count
