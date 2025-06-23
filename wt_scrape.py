import os
import aiohttp
from bs4 import BeautifulSoup

API_KEY = os.getenv('SCRAPPEY_API_KEY')

async def scrape_profile(session: aiohttp.ClientSession, nickname: str):
    if not API_KEY:
        raise RuntimeError('SCRAPPEY_API_KEY not configured')
    target_url = f'https://warthunder.com/en/community/userinfo/?nick={nickname}'
    url = 'https://scrappey.com/api/v1'
    params = {
        'api_key': API_KEY,
        'url': target_url,
        'render_js': 'false'
    }
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        resp.raise_for_status()
        html = await resp.text()
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    name_tag = soup.find(class_='profile-nickname')
    if name_tag:
        result['nickname'] = name_tag.get_text(strip=True)
    last_battle = soup.find(string=lambda t: 'Last played' in t)
    if last_battle:
        result['last_battle'] = last_battle.strip()
    return result

async def main():
    import asyncio, sys
    if len(sys.argv) != 2:
        print('Usage: python wt_scrape.py <nickname>')
        raise SystemExit(1)
    async with aiohttp.ClientSession() as session:
        data = await scrape_profile(session, sys.argv[1])
        print(data)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

