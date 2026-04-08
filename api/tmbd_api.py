import aiohttp
from config import TMDB_API_KEY


async def get_tmdb_movie_poster(title, year):
    """Fetches a movie poster from TMDB asynchronously."""
    if not TMDB_API_KEY:
        return None

    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "year": year
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results")
                    if results:
                        poster_path = results[0].get("poster_path")
                        if poster_path:
                            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        except Exception as e:
            print(f"⚠️ TMDB API Error (Movies): {e}")

    return None


async def get_tmdb_show_poster(title, year):
    """Fetches a TV show poster from TMDB asynchronously."""
    if not TMDB_API_KEY:
        return None

    url = "https://api.themoviedb.org/3/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        # TMDB uses 'first_air_date_year' for TV shows instead of 'year'
        "first_air_date_year": year
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results")
                    if results:
                        poster_path = results[0].get("poster_path")
                        if poster_path:
                            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        except Exception as e:
            print(f"⚠️ TMDB API Error (Shows): {e}")

    return None