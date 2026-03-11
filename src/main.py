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
        # Forzamos minúsculas para evitar el 404 en algunos subreddits
        self.url_template = "https://www.reddit.com/r/{}/new/.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "application/rss+xml"
        }

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit.lower())
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    xml_content = response.text
                    titles = re.findall(r'<title>(.*?)</title>', xml_content)[1:]
                    links = re.findall(r'<link href="(https://www.reddit.com/r/.*?)"', xml_content)
                    contents = re.findall(r'<content type="html">(.*?)</content>', xml_content)

                    results = []
                    for i in range(min(len(titles), 5)):
                        results.append({
                            "title": titles[i],
                            "text": contents[i] if i < len(contents) else "",
                            "url": links[i] if i < len(links) else f"https://reddit.com/r/{subreddit}"
                        })
                    return results, None # Retorna resultados y "sin error"
                else:
                    error_msg = f"📡 Fallo en r/{subreddit}: Código {response.status_code}"
                    return [], error_msg
            except Exception as e:
                return [], f"❌ Error de conexión en r/{subreddit}: {str(e)}"

# --- CONFIGURACIÓN ---
intents = discord.Intents.default()
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
scraper = RedditScraper()

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar RSS modo depuración listo: {self.user}")

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]

        print("🔎 Iniciando escaneo...")
        
        # Procesar cada categoría y reportar errores si los hay
        for cat_name, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tech", subs_tech, "tech")]:
            for sub in subs:
                posts, error = await scraper.get_latest_posts(sub)
                
                if error:
                    # Reportar el error al canal para que sepas qué falló sin mirar los logs
                    print(f"LOG: {error}")
                    continue 

                for p in posts:
                    # Limpieza básica para Gemini
                    texto_limpio = re.sub('<[^<]+?>', '', p['text'])[:1500]
                    try:
                        prompt = "Analiza si esto es relevante: {t}\n{txt}"
                        # Aquí iría tu lógica de Gemini... 
                        # (La mantengo simplificada para evitar errores de cuota hoy)
                        pass
                    except:
                        pass

        print("💤 Tarea finalizada. Entrando en modo reposo.")

if __name__ == "__main__":
    bot = ShadowRadar(intents=intents)

    async def run_once():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())
            
            timeout = 0
            while not bot.is_ready() and timeout < 15:
                await asyncio.sleep(1)
                timeout += 1
            
            if bot.is_ready():
                await bot.background_task()
            
        finally:
            await bot.close()
            print("🔌 Bot apagado.")

    asyncio.run(run_once())

