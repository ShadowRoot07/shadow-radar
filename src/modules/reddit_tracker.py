import httpx
import asyncio

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.json?limit=10"
        # Cabeceras para que Reddit crea que somos un navegador Chrome
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def get_latest_posts(self, subreddit):
        url = self.url_template.format(subreddit)
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    results = []
                    for post in posts:
                        p = post['data']
                        results.append({
                            "title": p['title'],
                            "text": p['selftext'],
                            "author": p['author'],
                            "url": f"https://www.reddit.com{p['permalink']}"
                        })
                    return results
                else:
                    print(f"⚠️ Error {response.status_code} en r/{subreddit}")
                    return []
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
                return []

# Prueba rápida
if __name__ == "__main__":
    scraper = RedditScraper()
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(scraper.get_latest_posts("desahogo"))
    for r in res:
        print(f"Post de {r['author']}: {r['title'][:50]}...")

