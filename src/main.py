import os
import asyncio
import discord
import httpx
import random
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

class RedditScraper:
    def __init__(self):
        # Intentamos con una URL más directa y sin el slash final antes del .rss
        # A veces Reddit prefiere /new.rss que /new/.rss
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
        }

    async def get_latest_posts(self, subreddit):
        # Aumentamos un poco el jitter para evitar detecciones
        await asyncio.sleep(random.uniform(3.0, 6.0))
        url = self.url_template.format(subreddit.lower())
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10.0) as client:
            try:
                response = await client.get(url)
                
                if response.status_code == 200:
                    xml_content = response.text
                    # Mejoramos la extracción para que sea más flexible
                    titles = re.findall(r'<title>(.*?)</title>', xml_content)
                    # El primer título suele ser el nombre del Subreddit, lo saltamos
                    titles = titles[1:] if len(titles) > 1 else titles
                    
                    links = re.findall(r'<link href="(https://www.reddit.com/r/[^"]+)"', xml_content)
                    contents = re.findall(r'<content type="html">(.*?)</content>', xml_content)

                    results = []
                    for i in range(min(len(titles), 5)):
                        results.append({
                            "title": titles[i] if i < len(titles) else "Sin título",
                            "text": contents[i] if i < len(contents) else "",
                            "url": links[i] if i < len(links) else f"https://reddit.com/r/{subreddit}"
                        })
                    return results, None
                
                elif response.status_code == 403:
                    return [], f"🚫 Acceso prohibido (403) en r/{subreddit}. Reddit bloqueó la IP."
                elif response.status_code == 404:
                    return [], f"❓ Subreddit r/{subreddit} no encontrado o sin RSS (404)."
                else:
                    return [], f"📡 Error HTTP {response.status_code} en r/{subreddit}."
                    
            except Exception as e:
                return [], f"❌ Error de conexión en r/{subreddit}: {str(e)}"

# --- CONFIGURACIÓN DE AI ---
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- BOT CORE ---
class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar Online: {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        # Limpieza de HTML para que Gemini no se pierda
        texto_plano = re.sub(r'<[^>]+>', '', texto)[:2000]
        if not texto_plano.strip(): return "NO"

        prompt = (PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH).format(texto=texto_plano)
        
        try:
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Error: No se pudo encontrar el canal de Discord.")
            return

        # Reducimos la lista para probar estabilidad
        subs_psico = ["desahogo", "psicologia"]
        subs_tech = ["programming", "technology"]

        scraper = RedditScraper()

        print("🔎 Iniciando escaneo de la mañana...")
        
        for cat, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tech", subs_tech, "tech")]:
            for sub in subs:
                print(f"📡 Solicitando r/{sub}...")
                posts, error = await scraper.get_latest_posts(sub)
                
                if error:
                    print(f"LOG: {error}")
                    continue

                for p in posts:
                    analisis = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo)
                    
                    if analisis != "NO" and "LIMITE" not in analisis:
                        await channel.send(f"📍 **Radar {cat} (r/{sub}):**\n{analisis}\n🔗 {p['url']}")
                        await asyncio.sleep(2) # Evitar spam en Discord

        print("💤 Tarea finalizada con éxito.")

# (El bloque de ejecución if __name__ == "__main__" se mantiene igual)

