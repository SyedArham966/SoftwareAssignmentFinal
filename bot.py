import os
import asyncio
import aiohttp
import time
from discord.ext import commands, tasks

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
API_BASE = os.getenv('PLAYER_API_ENDPOINT', 'https://api.thunderinsights.dk/v1')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', '0'))
PLAYER_NAMES = [name.strip() for name in os.getenv('PLAYER_NAMES', '').split(',') if name.strip()]
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '3600'))

intents = commands.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Simple cache for player search results to reduce API calls
PLAYER_CACHE: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 3600  # seconds

async def get_cached_player(session, name: str):
    key = name.lower()
    cached = PLAYER_CACHE.get(key)
    if cached and time.monotonic() - cached[1] < CACHE_TTL:
        return cached[0]
    player = await search_player(session, name)
    if player:
        PLAYER_CACHE[key] = (player, time.monotonic())
    return player

async def search_player(session, name: str):
    """Return the first player search result from Thunder Insights."""
    url = f"{API_BASE}/users/direct/search/"
    params = {"nick": name, "limit": 2}
    try:
        async with session.get(url, params=params, timeout=10) as resp:
            resp.raise_for_status()
            results = await resp.json()
            if isinstance(results, list) and results:
                return results[0]
    except Exception as e:
        print(f"Error searching for {name}: {e}")
    return None

async def fetch_player_stats(session, player_name: str):
    player = await get_cached_player(session, player_name)
    if not player:
        return None
    url = f"{API_BASE}/users/direct/{player['userid']}"
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            detail = await resp.json()
    except Exception as e:
        print(f"Error fetching player data: {e}")
        return None
    stats = detail.get("leaderboard", {}).get("tank_realistic", {}).get("value_total", {})
    return {
        "nickname": player.get("nick"),
        "kills": stats.get("kills_player_or_bot", {}).get("value_total"),
        "sessions": stats.get("each_player_session", {}).get("value_total"),
        "victories": stats.get("each_player_victories", {}).get("value_total"),
    }

async def refresh_user(session, userid: int):
    """Queue a data refresh for the given user."""
    url = f"{API_BASE}/users/refresh/{userid}"
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data[0].get("message")
    except Exception as e:
        print(f"Error refreshing user {userid}: {e}")
        return None

async def fetch_general_stats(session, player_name: str):
    """Return general stats for a player, refreshing if necessary."""
    player = await get_cached_player(session, player_name)
    if not player:
        return None
    url = f"{API_BASE}/users/stats/{player['userid']}"
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 404:
                await refresh_user(session, player['userid'])
                return None
            resp.raise_for_status()
            data = await resp.json()
    except Exception as e:
        print(f"Error fetching general stats: {e}")
        return None
    if not data:
        return None
    stats = data[0]
    return {
        "nickname": stats.get("nick"),
        "clan": stats.get("clan_tag"),
        "register_day": stats.get("register_day"),
        "last_update": stats.get("last_update"),
    }

async def fetch_player_units(session, player_name: str, gamemode: str | None = None):
    """Return list of unit stats for a player."""
    player = await get_cached_player(session, player_name)
    if not player:
        return None
    params = {}
    if gamemode:
        params["gamemode"] = gamemode
    url = f"{API_BASE}/users/stats/{player['userid']}/units/"
    try:
        async with session.get(url, params=params, timeout=10) as resp:
            if resp.status == 404:
                await refresh_user(session, player['userid'])
                return []
            resp.raise_for_status()
            return await resp.json()
    except Exception as e:
        print(f"Error fetching unit stats: {e}")
        return None


@bot.command()
async def player(ctx, *, player_name: str):
    """Fetch player stats from the API on demand."""
    await ctx.send(f"Fetching stats for {player_name}...")
    async with aiohttp.ClientSession() as session:
        stats = await fetch_player_stats(session, player_name)
    if stats:
        msg = (
            f"Stats for {stats['nickname']} -\n"
            f"Kills: {stats['kills']}\n"
            f"Victories: {stats['victories']}\n"
            f"Sessions: {stats['sessions']}"
        )
        await ctx.send(msg)
    else:
        await ctx.send("Could not retrieve stats.")

@bot.command()
async def stats(ctx, *, player_name: str):
    """Fetch general player stats, refreshing if necessary."""
    await ctx.send(f"Fetching general stats for {player_name}...")
    async with aiohttp.ClientSession() as session:
        data = await fetch_general_stats(session, player_name)
    if data:
        from datetime import datetime
        reg = datetime.utcfromtimestamp(data['register_day']).strftime('%Y-%m-%d') if data.get('register_day') else 'N/A'
        upd = datetime.utcfromtimestamp(data['last_update']).strftime('%Y-%m-%d %H:%M') if data.get('last_update') else 'N/A'
        clan = data['clan'] or 'None'
        msg = (
            f"General stats for {data['nickname']} -\n"
            f"Clan: {clan}\n"
            f"Registered: {reg}\n"
            f"Last update: {upd}"
        )
        await ctx.send(msg)
    else:
        await ctx.send("Stats not available yet; a refresh may have been queued.")

@bot.command()
async def refresh(ctx, *, player_name: str):
    """Queue a refresh for the given player."""
    async with aiohttp.ClientSession() as session:
        player = await get_cached_player(session, player_name)
        if not player:
            await ctx.send("Player not found")
            return
        msg = await refresh_user(session, player['userid'])
    await ctx.send(msg or "Refresh request failed")


@bot.command()
async def find(ctx, *, partial_name: str):
    """Search for players matching the given text."""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/users/direct/search/"
        params = {"nick": partial_name, "limit": 5}
        try:
            async with session.get(url, params=params, timeout=10) as resp:
                resp.raise_for_status()
                results = await resp.json()
        except Exception as e:
            print(f"Error searching players: {e}")
            results = []
    if not results:
        await ctx.send("No players found")
    else:
        lines = [f"{r['nick']} (ID {r['userid']})" for r in results]
        await ctx.send("\n".join(lines))


@bot.command()
async def units(ctx, player_name: str, gamemode: str | None = None, tier: int | None = None):
    """List a player's units filtered by gamemode and tier."""
    await ctx.send(f"Fetching units for {player_name}...")
    async with aiohttp.ClientSession() as session:
        data = await fetch_player_units(session, player_name, gamemode)
    if data is None:
        await ctx.send("Player not found or no unit data")
        return
    if tier is not None:
        data = [u for u in data if u.get("tier") == tier]
    if not data:
        await ctx.send("No units matching filters")
        return
    lines = []
    for unit in data[:10]:
        lines.append(f"{unit['name']} (Tier {unit['tier']}, {unit.get('gamemode','')})")
    if len(data) > 10:
        lines.append(f"...and {len(data)-10} more")
    await ctx.send("\n".join(lines))


@bot.command()
async def active(ctx, *, player_name: str):
    """Check if a player has been active in the last 30 days."""
    async with aiohttp.ClientSession() as session:
        stats = await fetch_general_stats(session, player_name)
    if not stats or not stats.get("last_update"):
        await ctx.send("Activity data unavailable")
        return
    from datetime import datetime, timezone
    last = datetime.fromtimestamp(stats["last_update"], tz=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - last
    status = "active" if delta.days < 30 else "inactive"
    await ctx.send(f"{stats['nickname']} was last seen {delta.days} days ago and is {status}.")

@tasks.loop(seconds=UPDATE_INTERVAL)
async def scheduled_updates():
    if CHANNEL_ID == 0 or not PLAYER_NAMES:
        return
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    async with aiohttp.ClientSession() as session:
        for name in PLAYER_NAMES:
            stats = await fetch_player_stats(session, name)
            if stats:
                msg = (
                    f"Scheduled stats for {stats['nickname']} -\n"
                    f"Kills: {stats['kills']}\n"
                    f"Victories: {stats['victories']}\n"
                    f"Sessions: {stats['sessions']}"
                )
                await channel.send(msg)

@bot.event
async def on_ready():
    if not scheduled_updates.is_running():
        scheduled_updates.start()
    print(f"Logged in as {bot.user}")

if __name__ == '__main__':
    if not TOKEN:
        raise SystemExit('DISCORD_BOT_TOKEN not set')
    bot.run(TOKEN)
