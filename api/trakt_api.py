import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-key": TRAKT_API_KEY,
    "trakt-api-version": "2"
}

async def get_recent_activity(username):
    url = f"https://api.trakt.tv/users/{username}/history?extended=images"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json() if response.status == 200 else None

async def get_full_history(username, media_type=None):
    page = 1
    per_page = 100
    all_history = []

    async with aiohttp.ClientSession() as session:
        while True:
            if media_type in ["movies", "shows", "episodes"]:
                url = f"https://api.trakt.tv/users/{username}/history/{media_type}"
            else:
                url = f"https://api.trakt.tv/users/{username}/history"

            url += f"?page={page}&limit={per_page}&extended=full"

            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"Error: {response.status} - {text}")
                    break

                page_data = await response.json()
                if not page_data:
                    break  # No more pages

                all_history.extend(page_data)
                page += 1

    return all_history

async def get_trakt_watchlist(username):
    url = f"https://api.trakt.tv/users/{username}/watchlist?extended=images"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json() if response.status == 200 else None

async def get_recent_history(username, media_type=None, page=1, per_page=100):
    if media_type in ["movies", "shows", "episodes"]:
        url = f"https://api.trakt.tv/users/{username}/history/{media_type}"
    else:
        url = f"https://api.trakt.tv/users/{username}/history"

    url += f"?page={page}&limit={per_page}&extended=full"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json() if response.status == 200 else []

async def get_now_playing(username):
    """Checks if a user is currently watching something on Trakt."""
    url = f"https://api.trakt.tv/users/{username}/watching"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_API_KEY
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                # Trakt returns 204 No Content if they aren't watching anything
                return None
        except Exception as e:
            print(f"⚠️ Trakt API Error (Now Playing): {e}")
            return None


async def get_user_stats(username):
    """Fetches a user's total watch time and stats from Trakt."""
    url = f"https://api.trakt.tv/users/{username}/stats"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"⚠️ Trakt API Error (Stats): {e}")
            return None

async def get_trakt_profile(username):
    """Fetches full Trakt profile including avatar images."""
    # We add ?extended=full to ensure we get the user's avatar URL
    url = f"https://api.trakt.tv/users/{username}?extended=full"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_API_KEY
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"⚠️ Trakt API Error (Profile): {e}")
            return None