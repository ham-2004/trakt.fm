import requests
import os
from dotenv import load_dotenv

load_dotenv()
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-key": TRAKT_API_KEY,
    "trakt-api-version": "2"
}

def get_recent_activity(username):
    url = f"https://api.trakt.tv/users/{username}/history?extended=images"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-key": TRAKT_API_KEY,
        "trakt-api-version": "2"
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_full_history(username, media_type=None):
    page = 1
    per_page = 100
    all_history = []

    while True:
        if media_type in ["movies", "shows", "episodes"]:
            url = f"https://api.trakt.tv/users/{username}/history/{media_type}"
        else:
            url = f"https://api.trakt.tv/users/{username}/history"

        url += f"?page={page}&limit={per_page}&extended=full"

        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        page_data = response.json()
        if not page_data:
            break  # No more pages

        all_history.extend(page_data)
        page += 1

    return all_history

def get_trakt_watchlist(username):
    url = f"https://api.trakt.tv/users/{username}/watchlist?extended=images"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-key": TRAKT_API_KEY,
        "trakt-api-version": "2"
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_recent_history(username, media_type=None, page=1, per_page=100):
    if media_type in ["movies", "shows", "episodes"]:
        url = f"https://api.trakt.tv/users/{username}/history/{media_type}"
    else:
        url = f"https://api.trakt.tv/users/{username}/history"

    url += f"?page={page}&limit={per_page}&extended=full"

    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []