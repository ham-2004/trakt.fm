import sqlite3

DB_FILE = "trakt_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. NEW: Create table for users mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            trakt_username TEXT NOT NULL
        )
    ''')

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
    cursor.execute('''
        INSERT OR REPLACE INTO users (discord_id, trakt_username)
        VALUES (?, ?)
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
        ORDER BY (movie_count + show_count) DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()
    return results