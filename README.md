# SoftwareAssignmentFinal

This project contains a small Discord bot example built with `discord.py`.
It attempts to fetch player statistics from the public
[Thunder Insights](https://thunderinsights.dk/) API and post them in a Discord
channel.

## Important disclaimer

Direct access to Gaijin and Statshark websites was unreliable in this
environment, so their Terms of Service could not be automatically reviewed.
The Thunder Insights API appeared accessible, but you should still check its
policies manually before using it in production.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables:
   - `DISCORD_BOT_TOKEN` – your Discord bot token.
   - `PLAYER_API_ENDPOINT` – base URL for the player statistics API
     (default: `https://api.thunderinsights.dk/v1`).
   - `DISCORD_CHANNEL_ID` – ID of the channel to post scheduled updates.
   - `PLAYER_NAMES` – comma-separated list of player names to poll.
   - `UPDATE_INTERVAL` – interval in seconds between automatic updates
     (default: 3600).
3. Run the bot with `python bot.py`.

### Adding the bot to a server

1. Create a new application at <https://discord.com/developers> and add a Bot
   user.
2. Enable the **Message Content Intent** for the bot.
3. Copy the application's **Client ID** and visit the following URL, replacing
   `YOUR_CLIENT_ID` with that value:

   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=2048
   ```

4. Choose a server where you have permission to add bots and authorize it.

The bot exposes several commands:

- `!player <name>` – shows basic kills, victories and sessions.
- `!stats <name>` – prints clan tag, registration date and last update time.
- `!refresh <name>` – queues a refresh on Thunder Insights.
- `!find <text>` – searches for users containing the text.
- `!units <name> [gamemode] [tier]` – lists the player’s units for a gamemode
  and tier.
- `!active <name>` – tells if the player has been active in the last 30 days.

Player IDs returned from searches are cached locally for an hour to minimize
requests to Thunder Insights.

The bot also posts periodic updates for names listed in `PLAYER_NAMES`.

## Other data sources

During manual research for community APIs and scraping tools, a few projects turned up:

- [Open Source API forum post](https://forum.warthunder.com/t/open-source-api/72519) references a GitHub repository (`wtpt-api`) that appears to be removed.
- [warthunder-scraper](https://github.com/pim97/warthunder-scraper) demonstrates scraping user profiles via the Scrappey service.
- [ThunderAPI](https://github.com/Suomalainen1976/thunderapi) is a Node.js scraper providing player and squadron info.

These tools rely on scraping the official website. You should review War Thunder's terms of service and each project's documentation before using them.

## Thunder Insights API

The public Thunder Insights API exposes a variety of endpoints for
retrieving user data. An OpenAPI specification is available at
<https://api.thunderinsights.dk/openapi.json> and the Swagger UI at
<https://api.thunderinsights.dk/docs>.

According to the documentation, responses are cached for roughly 20 hours.
Calling the `/v1/users/refresh/{userid}` endpoint queues a refresh, but the
data may not update until the cache expires.
