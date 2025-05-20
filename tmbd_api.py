import os
import requests
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def get_tmdb_movie_poster(title, year):
    """Search TMDB for a movie poster"""
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "year": year,
            "include_adult": False
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                poster_path = results[0].get("poster_path")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception as e:
        print(f"TMDB Search Error: {e}")
    return None

def get_tmdb_show_poster(title, year):
    """Search TMDB for a movie poster"""
    try:
        url = "https://api.themoviedb.org/3/search/tv"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "year": year,
            "include_adult": False
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                poster_path = results[0].get("poster_path")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception as e:
        print(f"TMDB Search Error: {e}")
    return None

def get_tmdb_person_poster(person_id):
    url = f"{TMDB_BASE_URL}/person/{person_id}/images"
    headers = {"Authorization": f"Bearer {TMDB_API_KEY}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        profiles = data.get("profiles", [])
        if profiles:
            return TMDB_IMAGE_BASE_URL + profiles[0]["file_path"]
    return None

