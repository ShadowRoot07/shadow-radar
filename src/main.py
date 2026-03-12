import os
import asyncio
import discord
import httpx
import random
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- PROMPTS (Faltaban en tu cat) ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post de Reddit. Si el autor muestra señales claras de crisis emocional,
necesidad de terapia profesional o problemas psicológicos serios, responde con un resumen
breve y profesional en ESPAÑOL. Si es un problema menor, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Analiza la siguiente noticia o post. Si es una noticia MUY destacable de tecnología,
IA o programación, responde con un resumen en ESPAÑOL.
Si no es relevante, responde "NO".
Post: {texto}
"""

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
        }

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(3.0, 6.0))
        url = self.url_template.format(subreddit.lower())
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    xml_content = response.text
                    titles = re.findall(r'<title>(.*?)</title>', xml_content)
                    titles = titles[1:] if len(titles) > 1 else titles
                    links = re.findall(r'<link href="(https://www.reddit.com/r/[^"]+)"', xml_content)
                    contents = re.findall(r'<content type="html">(.*?)</content>', xml_content)
                    results = []
                    for i in range(min(len(titles), 5)):
                        results.append({
                            "title": titles[i],
                            "text": contents[i] if i < len(contents) else "",
                            "url": links[i] if i < len(links) else f"https://reddit.com/r/{subreddit}"
                        })
                    return results, None
                return [], f"📡 Código {response.status_code} en r/{subreddit}"
            except Exception as e:
                return [], f"❌ Error: {str(e)}"

client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar Online: {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        texto_plano = re.sub(r'<[^>]+>', '', texto)[:2000]
        if not texto_plano.strip(): return "NO"
        prompt = (PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH).format(texto=texto_plano)
        try:
            response = client_ai.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return response.text.strip()
        except Exception:
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Error: Canal no encontrado.")
            return

        subs_psico = ["desahogo", "psicologia"]
        subs_tech = ["programming", "technology"]
        scraper = RedditScraper()

        print("🔎 Iniciando escaneo...")
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
                        await asyncio.sleep(2)
        print("💤 Tarea finalizada.")

# --- ESTE BLOQUE ES EL QUE FALTABA ---
if __name__ == "__main__":
    intents = discord.Intents.default()
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

