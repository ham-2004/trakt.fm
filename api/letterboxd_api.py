import re
import aiohttp
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BASE_URL = "https://letterboxd.com"

# Letterboxd (behind Cloudflare) may block the default aiohttp User-Agent
LB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

RSS_NS = {
    "letterboxd": "https://letterboxd.com",
    "tmdb": "https://themoviedb.org",
}


def format_stars(rating):
    """Formats a numeric rating like 3.5 into '★★★½'."""
    if rating is None:
        return None
    full = "★" * int(rating)
    half = "½" if rating % 1 else ""
    return full + half


async def letterboxd_user_exists(username):
    """Checks if a Letterboxd account exists (and its RSS feed is public)."""
    url = f"{BASE_URL}/{username}/rss/"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=LB_HEADERS) as response:
                return response.status == 200
        except Exception:
            return False


async def get_letterboxd_diary(username):
    """Fetches recent diary entries from the user's RSS feed (~50 latest)."""
    url = f"{BASE_URL}/{username}/rss/"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=LB_HEADERS) as response:
                if response.status != 200:
                    return None
                text = await response.text()
        except Exception as e:
            print(f"⚠️ Letterboxd RSS Error: {e}")
            return None

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        print(f"⚠️ Letterboxd RSS Parse Error: {e}")
        return None

    entries = []
    for item in root.iter("item"):
        title = item.findtext("letterboxd:filmTitle", namespaces=RSS_NS)
        watched_date = item.findtext("letterboxd:watchedDate", namespaces=RSS_NS)
        # The feed also contains created-list items (no filmTitle) and
        # review-only items without a watched date — skip both.
        if not title or not watched_date:
            continue

        rating_text = item.findtext("letterboxd:memberRating", namespaces=RSS_NS)
        try:
            rating = float(rating_text) if rating_text else None
        except ValueError:
            rating = None

        description = item.findtext("description") or ""
        poster_match = re.search(r'<img src="([^"]+)"', description)

        entries.append({
            "title": title,
            "year": item.findtext("letterboxd:filmYear", namespaces=RSS_NS),
            "rating": rating,
            "watched_date": watched_date,  # "YYYY-MM-DD"
            "rewatch": item.findtext("letterboxd:rewatch", namespaces=RSS_NS) == "Yes",
            "link": item.findtext("link"),
            "tmdb_id": item.findtext("tmdb:movieId", namespaces=RSS_NS),
            "poster_url": poster_match.group(1) if poster_match else None,
        })

    return entries


async def get_letterboxd_profile_stats(username):
    """Scrapes profile stats (films, this year, lists, followers...) from the profile page."""
    url = f"{BASE_URL}/{username}/"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=LB_HEADERS) as response:
                if response.status != 200:
                    return None
                html = await response.text()
        except Exception as e:
            print(f"⚠️ Letterboxd Profile Error: {e}")
            return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Stats keyed by their label text so a reordering on the page doesn't break us
        stats = {}
        for block in soup.select("h4.profile-statistic"):
            value = block.select_one("span.value")
            definition = block.select_one("span.definition")
            if value and definition:
                stats[definition.get_text(strip=True).lower()] = value.get_text(strip=True)

        avatar = None
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            avatar = og_image.get("content")
        if not avatar:
            avatar_img = soup.select_one("div.profile-avatar img")
            if avatar_img:
                avatar = avatar_img.get("src")

        display_name = None
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title:
            display_name = og_title.get("content")
            if display_name:
                # og:title is "Name’s profile"
                display_name = re.sub(r"[’']s profile$", "", display_name).strip()

        location = None
        location_el = soup.select_one("div.profile-metadata .metadatum .label")
        if location_el:
            location = location_el.get_text(strip=True)

        return {
            "films": stats.get("films"),
            "this_year": stats.get("this year"),
            "lists": stats.get("lists"),
            "following": stats.get("following"),
            "followers": stats.get("followers"),
            "avatar": avatar,
            "display_name": display_name,
            "location": location,
        }
    except Exception as e:
        print(f"⚠️ Letterboxd Profile Parse Error: {e}")
        return None


async def get_letterboxd_watchlist(username, max_pages=5):
    """Scrapes the user's watchlist pages. Returns [{'title', 'year', 'slug'}, ...]."""
    films = []
    async with aiohttp.ClientSession() as session:
        for page in range(1, max_pages + 1):
            url = f"{BASE_URL}/{username}/watchlist/page/{page}/"
            try:
                async with session.get(url, headers=LB_HEADERS) as response:
                    if response.status != 200:
                        break
                    html = await response.text()
            except Exception as e:
                print(f"⚠️ Letterboxd Watchlist Error: {e}")
                break

            soup = BeautifulSoup(html, "html.parser")
            posters = soup.select("li.griditem div.react-component[data-item-slug]")
            if not posters:
                # Older grid markup, kept as fallback
                posters = soup.select("li.poster-container div.film-poster[data-film-slug]")
            if not posters:
                break

            for poster in posters:
                slug = poster.get("data-item-slug") or poster.get("data-film-slug")
                name = poster.get("data-item-name")
                if not name:
                    img = poster.select_one("img")
                    name = img.get("alt") if img else None
                if not name or not slug:
                    continue

                # data-item-name looks like "Film Title (2026)"
                match = re.match(r"^(.*?)\s*\((\d{4})\)$", name)
                if match:
                    title, year = match.group(1), match.group(2)
                else:
                    title, year = name, None

                films.append({"title": title, "year": year, "slug": slug})

    return films


async def get_letterboxd_film_poster(slug):
    """Fetches the poster URL for a film slug from the film page's JSON-LD.

    The watchlist HTML only has placeholder posters (real ones are injected
    client-side) and the old ajax poster endpoint is gone, so we read the
    schema.org metadata on the film page instead.
    """
    url = f"{BASE_URL}/film/{slug}/"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=LB_HEADERS) as response:
                if response.status != 200:
                    return None
                html = await response.text()
        except Exception as e:
            print(f"⚠️ Letterboxd Poster Error: {e}")
            return None

    # JSON-LD "image" is the true 2:3 poster; og:image is a landscape crop
    match = re.search(r'"image":"(https://a\.ltrbxd\.com/[^"]+)"', html)
    if match and "empty-poster" not in match.group(1):
        return match.group(1)
    return None
