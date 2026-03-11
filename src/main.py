import os
import asyncio
import discord
import httpx
import random
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- SCRAPER VÍA RSS (EL SALTO DEFINITIVO AL 403) ---
class RedditScraper:
    def __init__(self):
        # Usamos la URL de RSS en lugar de JSON
        self.url_template = "https://www.reddit.com/r/{}/new/.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/121.0 ShadowRadar/1.2",
            "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit)
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    xml_content = response.text
                    
                    # Extraemos títulos, links y contenido usando Regex simple
                    # Buscamos patrones de <entry> en el XML de Reddit
                    titles = re.findall(r'<title>(.*?)</title>', xml_content)[1:] # El primero suele ser el nombre del sub
                    links = re.findall(r'<link href="(https://www.reddit.com/r/.*?)"', xml_content)
                    contents = re.findall(r'<content type="html">(.*?)</content>', xml_content)

                    results = []
                    # Emparejamos los datos encontrados
                    for i in range(min(len(titles), 5)):
                        results.append({
                            "title": titles[i],
                            "text": contents[i] if i < len(contents) else "",
                            "url": links[i] if i < len(links) else f"https://reddit.com/r/{subreddit}"
                        })
                    return results
                else:
                    print(f"⚠️ Error {response.status_code} en r/{subreddit} (RSS)")
                    return []
            except Exception as e:
                print(f"❌ Error en RSS r/{subreddit}: {e}")
                return []

# --- CONFIGURACIÓN DE CLIENTES ---
intents = discord.Intents.default()
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
scraper = RedditScraper()

# --- PROMPTS ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post. Si el autor muestra señales claras de crisis emocional,
necesidad de terapia profesional o problemas psicológicos serios, responde con un resumen
breve y profesional en ESPAÑOL. Si es un problema menor, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Analiza la siguiente noticia. Si es una noticia MUY destacable de tecnología,
IA o programación, responde con un resumen en ESPAÑOL. 
Si no es relevante, responde "NO".
Post: {texto}
"""

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar RSS encendido como {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        # Limpiamos un poco el HTML que viene del RSS para que Gemini no se confunda
        texto_limpio = re.sub('<[^<]+?>', '', texto)[:2000] 
        try:
            prompt = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt.format(texto=texto_limpio)
            )
            return response.text.strip()
        except Exception as e:
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        subs_psico = ["desahogo", "psicologia", "Ayuda"]
        subs_tech = ["programming", "technology", "Python"]

        print("🔎 Escaneando via RSS...")
        for sub in subs_psico:
            posts = await scraper.get_latest_posts(sub)
            for p in posts:
                res = await self.filtrar_con_ai(f"{p['title']} {p['text']}", "psico")
                if res != "NO" and "LIMITE" not in res:
                    await channel.send(f"⚠️ **Oportunidad Terapéutica (r/{sub}):**\n{res}\n🔗 {p['url']}")

        for sub in subs_tech:
            posts = await scraper.get_latest_posts(sub)
            for t in posts:
                res = await self.filtrar_con_ai(t['title'], "tech")
                if res != "NO" and "LIMITE" not in res:
                    await channel.send(f"🚀 **Radar Tech (r/{sub}):**\n{res}\n🔗 {t['url']}")

# --- EJECUCIÓN ---
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

    asyncio.run(run_once())

