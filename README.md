# Trakt.fm Discord Bot 🎬

A Discord bot that integrates with Trakt.tv to show what you and your server members are watching, generate aesthetic image grids of recent watches, and maintain a server leaderboard.

## Features
* **Now Playing:** See what you are currently watching in real-time.
* **Watch History Grids:** Generate visual grids of your 6 most recently watched movies or shows.
* **Server Leaderboard:** Compete with server members to see who has the most scrobbles.
* **Interactive Watchlist:** Browse your Trakt watchlist directly in Discord.
* **Detailed Profiles:** View watch time, engagement stats, and user ranks.

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys.
4. Run the bot: `python bot.py`

## Commands
* `/help` or `!help` — Show help message
* `/tset <username>` — Link your Trakt username
* `/tr` — Show your most recently watched item
* `/t6` — Show your six recently watched movies (Image Grid)
* `/t6s` — Show your six recently watched shows (Image Grid)
* `/tw` — View your interactive Trakt watchlist
* `/np` — See what you are currently watching
* `/top` — View the server-wide Trakt leaderboard
* `/profile` — View your detailed Trakt profile and stats