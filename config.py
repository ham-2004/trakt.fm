import os
from dotenv import load_dotenv

load_dotenv()

TRAKT_API_KEY = os.getenv("TRAKT_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

FALLBACK_POSTER = "https://i.imgur.com/Z2MYNbj.png"
IMAGE_CACHE_DIR = "image_cache"