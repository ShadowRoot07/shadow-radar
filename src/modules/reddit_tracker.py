import httpx
import asyncio
import random
import re
from datetime import datetime, timezone

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        # User-Agent rotado para mayor seguridad
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"}

    async def get_latest_posts(self, subreddit):
        # Respiro antes de consultar Reddit
        await asyncio.sleep(random.uniform(1.0, 3.0))
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
                        # Filtro estricto: solo lo que tiene menos de 40 minutos
                        diff_minutes = (datetime.now(timezone.utc) - dt_updated).total_seconds() / 60
                        
                        if diff_minutes <= 500:
                            title = re.search(r'<title>(.*?)</title>', entry).group(1)
                            # Limpiar entidades HTML básicas del título
                            title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                            
                            link_match = re.search(r'<link href="(https://www.reddit.com/r/[^"]+)"', entry)
                            link = link_match.group(1) if link_match else ""
                            
                            content = re.search(r'<content type="html">(.*?)</content>', entry, re.DOTALL)
                            # Solo guardamos los primeros 1000 caracteres para no inflar el prompt
                            text = content.group(1)[:1000] if content else ""

                            results.append({
                                "title": title,
                                "text": text,
                                "url": link
                            })
                    return results, None
                return [], f"Error {response.status_code}"
            except Exception as e:
                return [], str(e)

