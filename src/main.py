import os
import asyncio
import discord
import httpx
import random
import re
from datetime import datetime, timezone
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- PROMPTS RESTRICTIVOS (VUELVEN A LA NORMALIDAD) ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post. Si el autor muestra señales de crisis emocional seria, 
necesidad de terapia o problemas psicológicos graves, resume en ESPAÑOL. 
Si no es urgente, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Si esta es una noticia de tecnología o programación REALMENTE relevante o novedosa, 
resúmela en ESPAÑOL. Si es una duda simple o poco importante, responde "NO".
Post: {texto}
"""

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        }

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit.lower())
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    xml = response.text
                    # Extraer bloques de entrada <entry>...</entry>
                    entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
                    results = []
                    
                    for entry in entries:
                        # Extraer fecha de actualización
                        updated_str = re.search(r'<updated>(.*?)</updated>', entry).group(1)
                        # Formato: 2026-03-12T13:00:00+00:00
                        dt_updated = datetime.fromisoformat(updated_str)
                        ahora = datetime.now(timezone.utc)
                        diferencia_minutos = (ahora - dt_updated).total_seconds() / 60

                        # SOLO POSTS DE LA ÚLTIMA HORA (60 min)
                        if diferencia_minutos <= 60:
                            title = re.search(r'<title>(.*?)</title>', entry).group(1)
                            link = re.search(r'<link href="(https://www.reddit.com/r/[^"]+)"', entry).group(1)
                            content = re.search(r'<content type="html">(.*?)</content>', entry, re.DOTALL)
                            results.append({
                                "title": title,
                                "text": content.group(1) if content else "",
                                "url": link
                            })
                    return results, None
                return [], f"📡 Código {response.status_code}"
            except Exception as e:
                return [], str(e)

client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class ShadowRadar(discord.Client):
    quota_exceeded = False # Bandera para dejar de llamar a Gemini si da 429

    async def filtrar_con_ai(self, texto, tipo="psico"):
        if self.quota_exceeded: return "QUOTA_ERROR"
        
        texto_plano = re.sub(r'<[^>]+>', '', texto).strip()[:1500]
        prompt_base = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        
        try:
            # Delay anti-spam para la API (2 segundos entre llamadas)
            await asyncio.sleep(2) 
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt_base.format(texto=texto_plano)
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        await channel.send("🛰️ **Shadow Radar:** Iniciando patrullaje de posts recientes (última hora)...")

        subs_psico = ["desahogo", "psicologia"]
        subs_tech = ["programming", "technology", "python"]
        scraper = RedditScraper()

        for cat, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tecnología", subs_tech, "tech")]:
            for sub in subs:
                posts, _ = await scraper.get_latest_posts(sub)
                for p in posts:
                    res = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo)
                    
                    if res == "QUOTA_ERROR":
                        await channel.send("⚠️ **Aviso:** Se ha agotado la cuota de Gemini por ahora. El resto de posts se ignorarán.")
                        return # Abortar escaneo para no saturar más

                    if res and res.upper() != "NO":
                        emoji = "🧠" if tipo == "psico" else "💻"
                        await channel.send(f"{emoji} **Radar {cat} (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        await channel.send("🏁 **Patrullaje finalizado.**")

if __name__ == "__main__":
    bot = ShadowRadar(intents=discord.Intents.default())
    async def run():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())
            for _ in range(15):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            if bot.is_ready(): await bot.background_task()
        finally:
            await bot.close()
    asyncio.run(run())

