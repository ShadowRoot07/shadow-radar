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

# --- PROMPTS DE ALTA RELEVANCIA ---
PROMPT_PSICOLOGIA = """
Analiza este post. Si el autor muestra señales de crisis emocional grave o riesgo, 
resume en ESPAÑOL de forma profesional. Si es un desahogo común o no es urgente, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Si esta noticia es un hito importante en IA, programación o tecnología (no dudas simples), 
resúmela en ESPAÑOL. Si no es altamente relevante, responde "NO".
Post: {texto}
"""

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
                        ahora = datetime.now(timezone.utc)
                        # FILTRO DE 6 HORAS (360 minutos)
                        if (ahora - dt_updated).total_seconds() / 60 <= 360:
                            title = re.search(r'<title>(.*?)</title>', entry).group(1)
                            link = re.search(r'<link href="(https://www.reddit.com/r/[^"]+)"', entry).group(1)
                            content = re.search(r'<content type="html">(.*?)</content>', entry, re.DOTALL)
                            results.append({"title": title, "text": content.group(1) if content else "", "url": link})
                    return results, None
                return [], f"Error {response.status_code}"
            except Exception as e:
                return [], str(e)

client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class ShadowRadar(discord.Client):
    quota_exceeded = False

    async def filtrar_con_ai(self, texto, tipo="psico"):
        if self.quota_exceeded: return "QUOTA_ERROR"
        texto_plano = re.sub(r'<[^>]+>', '', texto).strip()[:1500]
        prompt_base = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        try:
            await asyncio.sleep(2) 
            response = client_ai.models.generate_content(model="gemini-2.0-flash", contents=prompt_base.format(texto=texto_plano))
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "QUOTA" in str(e).upper():
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        await channel.send("🚀 **Shadow Radar:** Iniciando patrullaje de las últimas 6 horas...")

        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]
        scraper = RedditScraper()

        for cat, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tecnología", subs_tech, "tech")]:
            for sub in subs:
                posts, _ = await scraper.get_latest_posts(sub)
                for p in posts:
                    res = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo)
                    if res == "QUOTA_ERROR":
                        await channel.send("⚠️ **Fuera de Servicio:** Cuota de Gemini agotada (Error 429).")
                        return 
                    if res and res.upper() != "NO":
                        emoji = "🧠" if tipo == "psico" else "💻"
                        await channel.send(f"{emoji} **Radar {cat} (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        await channel.send("🏁 **Patrullaje finalizado.** Siguiente revisión en 6 horas.")

if __name__ == "__main__":
    bot = ShadowRadar(intents=discord.Intents.default())
    async def run_once():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())
            for _ in range(15):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            if bot.is_ready(): await bot.background_task()
        finally:
            await bot.close()
    asyncio.run(run_once())

