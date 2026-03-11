import httpx
import asyncio
import random

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.json?limit=10"
        # Cabeceras mucho más realistas y completas
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def get_latest_posts(self, subreddit):
        # Pequeña pausa aleatoria para no parecer un script automatizado
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        url = self.url_template.format(subreddit)
        
        # Usamos follow_redirects=True para evitar bloqueos por redirección
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    results = []
                    for post in posts:
                        p = post['data']
                        results.append({
                            "title": p.get('title', ''),
                            "text": p.get('selftext', ''),
                            "author": p.get('author', 'Desconocido'),
                            "url": f"https://www.reddit.com{p.get('permalink', '')}"
                        })
                    return results
                
                elif response.status_code == 429:
                    print(f"🛑 Reddit nos dio Rate Limit (429) en r/{subreddit}. Bajando velocidad...")
                    return []
                else:
                    print(f"⚠️ Error {response.status_code} en r/{subreddit}")
                    return []
                    
            except Exception as e:
                print(f"❌ Error de conexión en r/{subreddit}: {e}")
                return []

# --- LÓGICA DE ESCANEO RECOMENDADA PARA MAIN.PY ---
# Cuando lo llames desde main.py, hazlo así:
# subreddits = ["desahogo", "psicologia", "Ayuda"]
# for sub in subreddits:
#     res = await scraper.get_latest_posts(sub)
#     # ... procesar ...

