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

# --- PROMPTS DE PRODUCCIÓN ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post. Si el autor muestra señales de crisis emocional seria, 
necesidad de terapia o problemas psicológicos graves, resume en ESPAÑOL. 
Si no es urgente o es trivial, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Si esta es una noticia de tecnología o programación REALMENTE relevante, innovadora 
o de gran impacto, resúmela en ESPAÑOL. Si es una duda simple, responde "NO".
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
                    entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
                    results = []
                    
                    for entry in entries:
                        # Extraer fecha
                        updated_match = re.search(r'<updated>(.*?)</updated>', entry)
                        if not updated_match: continue
                        
                        dt_updated = datetime.fromisoformat(updated_match.group(1))
                        ahora = datetime.now(timezone.utc)
                        diferencia_minutos = (ahora - dt_updated).total_seconds() / 60

                        # Solo posts de la última hora
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
            await asyncio.sleep(2) # Respetar RPM de Gemini
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt_base.format(texto=texto_plano)
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "QUOTA" in str(e).upper():
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        # 1. Mensaje de Encendido
        await channel.send("🚀 **Shadow Radar Online:** Iniciando patrullaje preventivo...")

        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]
        scraper = RedditScraper()

        for cat, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tecnología", subs_tech, "tech")]:
            for sub in subs:
                posts, _ = await scraper.get_latest_posts(sub)
                for p in posts:
                    res = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo)
                    
                    if res == "QUOTA_ERROR":
                        # 2. Mensaje si se acaban las cuotas
                        await channel.send("⚠️ **Límite Alcanzado:** Gemini ha agotado la cuota de peticiones (Error 429). El patrullaje se detendrá aquí.")
                        return 

                    if res and res.upper() != "NO":
                        emoji = "🧠" if tipo == "psico" else "💻"
                        await channel.send(f"{emoji} **Radar {cat} (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        # 3. Mensaje de Finalización
        await channel.send("🏁 **Patrullaje Completado:** Todos los subreddits han sido revisados. Entrando en modo reposo.")

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
            print("🔌 Bot desconectado.")
    asyncio.run(run())

