from database.database import save_history_to_db

def save_recent_trakt_data(username, history):
    recent_movies = [entry for entry in history if 'movie' in entry]
    recent_shows = [entry for entry in history if 'show' in entry]
    save_history_to_db(username, recent_shows, recent_movies)
