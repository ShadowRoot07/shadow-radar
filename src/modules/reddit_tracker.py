import httpx
import asyncio
import random

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.json?limit=5"
        # Engañamos a Reddit pretendiendo ser el bot de inspección de Google
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }


    async def get_latest_posts(self, subreddit):
        # Pausa obligatoria: GitHub es demasiado rápido
        await asyncio.sleep(random.uniform(2, 4))
        
        url = self.url_template.format(subreddit)
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                # Simulamos que venimos referidos de una búsqueda
                response = await client.get(url, params={"rdt": "43210"}) 
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {}).get('children', [])
                else:
                    print(f"⚠️ Error {response.status_code} en r/{subreddit}")
                    return []
            except Exception as e:
                print(f"❌ Error en r/{subreddit}: {e}")
                return []

