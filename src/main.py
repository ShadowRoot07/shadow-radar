import os
import asyncio
import discord
import httpx
import random
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- SCRAPER CON CAMUFLAJE DE GOOGLEBOT ---
class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.json?limit=5"
        # Usamos la identidad de Googlebot para que Reddit nos deje pasar
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5"
        }

    async def get_latest_posts(self, subreddit):
        # Pausa aleatoria para no saturar y parecer humano/bot legal
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit)
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                # El parámetro rdt ayuda a veces a saltar checks de redirección
                response = await client.get(url, params={"rdt": "45120"})
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    results = []
                    for post in posts:
                        p = post['data']
                        results.append({
                            "title": p.get('title', ''),
                            "text": p.get('selftext', ''),
                            "url": f"https://www.reddit.com{p.get('permalink', '')}"
                        })
                    return results
                else:
                    print(f"⚠️ Error {response.status_code} en r/{subreddit}")
                    return []
            except Exception as e:
                print(f"❌ Error de conexión en r/{subreddit}: {e}")
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
        if not channel: 
            print("❌ Canal no encontrado")
            return

        subs_psico = ["desahogo", "psicologia", "Ayuda"]
        subs_tech = ["programming", "technology", "Python"]

        # --- SECCIÓN PSICOLOGÍA ---
        print("🔎 Buscando casos para tu padre...")
        for sub in subs_psico:
            posts = await scraper.get_latest_posts(sub)
            for p in posts: # Aquí 'p' ya es el diccionario limpio
                contenido = f"Título: {p['title']}\nContenido: {p['text']}"
                res = await self.filtrar_con_ai(contenido, "psico")

                if res == "LIMITE_ALCANZADO": 
                    print("🛑 Límite de IA alcanzado.")
                    return
                if res != "NO":
                    await channel.send(f"⚠️ **Oportunidad Terapéutica:**\n{res}\n🔗 {p['url']}")

        # --- SECCIÓN TECH ---
        print("🔎 Buscando noticias Tech...")
        for sub in subs_tech:
            posts = await scraper.get_latest_posts(sub)
            for t in posts:
                res = await self.filtrar_con_ai(t['title'], "tech")

                if res == "LIMITE_ALCANZADO": 
                    print("🛑 Límite de IA alcanzado.")
                    return
                if res != "NO":
                    await channel.send(f"🚀 **Radar Tech:**\n{res}\n🔗 {t['url']}")

# --- LÓGICA DE EJECUCIÓN ---
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
                print("✅ Tarea completada.")
            else:
                print("❌ No se pudo conectar a Discord.")
        finally:
            await bot.close()
            print("🔌 Sesión cerrada.")

    asyncio.run(run_once())

