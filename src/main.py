import os
import asyncio
import discord
import httpx
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- TU SCRAPER DE REDDIT ---
class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.json?limit=10"
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

# --- CONFIGURACIÓN DE CLIENTES ---
intents = discord.Intents.default()
intents.message_content = True
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
scraper = RedditScraper()

# --- PROMPTS ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post de Reddit. Si el autor muestra señales claras de crisis emocional, 
necesidad de terapia profesional o problemas psicológicos serios, responde con un resumen 
breve y profesional en ESPAÑOL. Si es un problema menor, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Analiza la siguiente noticia o post. Si es una noticia MUY destacable de tecnología, 
IA o programación, responde con un resumen en ESPAÑOL (traduce si es necesario). 
Si no es relevante, responde "NO".
Post: {texto}
"""

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar encendido como {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        try:
            prompt = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt.format(texto=texto)
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                return "LIMITE_ALCANZADO"
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        # --- ESCANEO DE PSICOLOGÍA ---
        print("🔎 Buscando casos para tu padre...")
        posts_psico = await scraper.get_latest_posts("desahogo+psicologia+ayuda")
        for p in posts_psico:
            # Combinamos título y texto para que Gemini tenga todo el contexto
            contenido = f"Título: {p['title']}\nContenido: {p['text']}"
            res = await self.filtrar_con_ai(contenido, "psico")
            
            if res == "LIMITE_ALCANZADO":
                await channel.send("🛑 Cuota de IA agotada.")
                return
            if res != "NO":
                await channel.send(f"⚠️ **Oportunidad Terapéutica:**\n{res}\n🔗 {p['url']}")

        # --- ESCANEO DE TECH ---
        print("🔎 Buscando noticias Tech...")
        posts_tech = await scraper.get_latest_posts("programming+technology+Python")
        for t in posts_tech:
            res = await self.filtrar_con_ai(t['title'], "tech")
            
            if res == "LIMITE_ALCANZADO":
                await channel.send("🛑 Cuota de IA agotada.")
                return
            if res != "NO":
                await channel.send(f"🚀 **Radar Tech:**\n{res}\n🔗 {t['url']}")

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

