import sqlite3

DB_FILE = "trakt_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. NEW: Create table for users mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            trakt_username TEXT,
            letterboxd_username TEXT
        )
    ''')

    # Migrate pre-Letterboxd databases: the old schema had trakt_username NOT NULL
    # and no letterboxd_username column. SQLite can't drop NOT NULL via ALTER,
    # so rebuild the table once.
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "letterboxd_username" not in columns:
        cursor.execute("ALTER TABLE users RENAME TO users_old")
        cursor.execute('''
            CREATE TABLE users (
                discord_id TEXT PRIMARY KEY,
                trakt_username TEXT,
                letterboxd_username TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO users (discord_id, trakt_username)
            SELECT discord_id, trakt_username FROM users_old
        ''')
        cursor.execute("DROP TABLE users_old")

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

# --- NEW USER HELPER FUNCTIONS ---

def save_user(discord_id, trakt_username):
    """Saves or updates a user's Trakt username"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Upsert instead of INSERT OR REPLACE: REPLACE deletes the row first,
    # which would wipe the letterboxd_username column.
    cursor.execute('''
        INSERT INTO users (discord_id, trakt_username)
        VALUES (?, ?)
        ON CONFLICT(discord_id) DO UPDATE SET trakt_username = excluded.trakt_username
    ''', (str(discord_id), trakt_username))
    conn.commit()
    conn.close()

def get_user(discord_id):
    """Fetches a Trakt username by Discord ID"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT trakt_username FROM users WHERE discord_id = ?', (str(discord_id),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def delete_user(discord_id):
    """Removes a user's Trakt link, keeping the row if Letterboxd is still linked."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET trakt_username = NULL WHERE discord_id = ?', (str(discord_id),))
    cursor.execute('''
        DELETE FROM users
        WHERE discord_id = ? AND trakt_username IS NULL AND letterboxd_username IS NULL
    ''', (str(discord_id),))
    conn.commit()
    conn.close()

def save_letterboxd_user(discord_id, letterboxd_username):
    """Saves or updates a user's Letterboxd username"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (discord_id, letterboxd_username)
        VALUES (?, ?)
        ON CONFLICT(discord_id) DO UPDATE SET letterboxd_username = excluded.letterboxd_username
    ''', (str(discord_id), letterboxd_username))
    conn.commit()
    conn.close()

def get_letterboxd_user(discord_id):
    """Fetches a Letterboxd username by Discord ID"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT letterboxd_username FROM users WHERE discord_id = ?', (str(discord_id),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def delete_letterboxd_user(discord_id):
    """Removes a user's Letterboxd link, keeping the row if Trakt is still linked."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET letterboxd_username = NULL WHERE discord_id = ?', (str(discord_id),))
    cursor.execute('''
        DELETE FROM users
        WHERE discord_id = ? AND trakt_username IS NULL AND letterboxd_username IS NULL
    ''', (str(discord_id),))
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


def get_leaderboard(limit=10):
    """Fetches the top users ranked by total scrobbles (movies + shows)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # We use a SQL subquery to count movies and shows for each user instantly
    cursor.execute('''
        SELECT u.discord_id, u.trakt_username,
               (SELECT COUNT(*) FROM movies m WHERE m.username = u.trakt_username) as movie_count,
               (SELECT COUNT(*) FROM shows s WHERE s.username = u.trakt_username) as show_count
        FROM users u
        WHERE u.trakt_username IS NOT NULL
        ORDER BY (movie_count + show_count) DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()
    return results