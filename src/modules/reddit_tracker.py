import httpx
import asyncio
import random
import re
from datetime import datetime, timezone

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/123.0"}

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit.lower())
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    entries = re.findall(r'<entry>(.*?)</entry>', response.text, re.DOTALL)
                    results = []
                    for entry in entries:
                        updated_match = re.search(r'<updated>(.*?)</updated>', entry)
                        if not updated_match: continue
                        
                        dt_updated = datetime.fromisoformat(updated_match.group(1))
                        # Filtro de 35 minutos para el cron de 30
                        if (datetime.now(timezone.utc) - dt_updated).total_seconds() / 60 <= 35:
                            title = re.search(r'<title>(.*?)</title>', entry).group(1)
                            link = re.search(r'<link href="(https://www.reddit.com/r/[^"]+)"', entry).group(1)
                            content = re.search(r'<content type="html">(.*?)</content>', entry, re.DOTALL)
                            results.append({
                                "title": title, 
                                "text": content.group(1) if content else "", 
                                "url": link
                            })
                    return results, None
                return [], f"Error {response.status_code}"
            except Exception as e:
                return [], str(e)

