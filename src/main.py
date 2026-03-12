import os
import asyncio
import discord
import httpx
import random
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- PROMPTS OPTIMIZADOS ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post de Reddit. Si el autor muestra señales claras de crisis emocional,
necesidad de terapia profesional o problemas psicológicos serios, responde con un resumen
breve y profesional en ESPAÑOL. Si no es un caso serio o es solo una duda trivial, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Resume este post de tecnología/programación en una sola oración concisa en ESPAÑOL. 
Si el texto no tiene contenido informativo útil o es publicidad, responde "NO".
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

# Configuración Global
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar Online: {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        # Limpieza profunda de HTML y entidades XML para Gemini
        texto_plano = re.sub(r'<[^>]+>', '', texto)
        texto_plano = texto_plano.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        texto_plano = texto_plano.strip()[:2000]
        
        if not texto_plano: return "NO"
        
        prompt_base = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        try:
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt_base.format(texto=texto_plano)
            )
            return response.text.strip()
        except Exception:
            return "NO"

    async def background_task(self):
        channel_id = os.getenv("DISCORD_CHANNEL_ID")
        channel = self.get_channel(int(channel_id))
        if not channel:
            print(f"❌ Error: Canal {channel_id} no encontrado.")
            return

        # Prueba de vida inicial
        await channel.send("🛰️ **Shadow Radar reportándose:** Iniciando patrullaje de subreddits...")

        subs_psico = ["desahogo", "psicologia"]
        subs_tech = ["programming", "technology", "python"]
        scraper = RedditScraper()

        print("🔎 Iniciando escaneo...")
        
        # Categorías a escanear
        categorias = [
            ("Psicología", subs_psico, "psico"),
            ("Tecnología", subs_tech, "tech")
        ]

        for nombre_cat, lista_subs, tipo_ai in categorias:
            for sub in lista_subs:
                print(f"📡 Solicitando r/{sub}...")
                posts, error = await scraper.get_latest_posts(sub)
                
                if error:
                    print(f"LOG: {error}")
                    continue

                for p in posts:
                    analisis = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo_ai)
                    
                    if analisis and analisis.upper() != "NO":
                        # Formatear el mensaje para Discord
                        emoji = "🧠" if tipo_ai == "psico" else "💻"
                        mensaje = (
                            f"{emoji} **Oportunidad en r/{sub}** ({nombre_cat}):\n"
                            f"> {analisis}\n"
                            f"🔗 [Ir al post]({p['url']})"
                        )
                        await channel.send(mensaje)
                        await asyncio.sleep(1) # Pequeño respiro entre mensajes

        print("💤 Tarea finalizada.")
        await channel.send("📡 **Patrullaje finalizado:** Entrando en modo reposo.")

if __name__ == "__main__":
    intents = discord.Intents.default()
    # No necesitamos intents de mensajes si solo enviamos, pero lo dejamos por defecto
    bot = ShadowRadar(intents=intents)

    async def run_once():
        try:
            # Login y conexión manual para correr como script único
            await bot.login(os.getenv("DISCORD_TOKEN"))
            # Creamos la conexión en segundo plano
            asyncio.create_task(bot.connect())
            
            # Esperar a que el bot esté listo (máximo 20 seg)
            for _ in range(20):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            
            if bot.is_ready():
                await bot.background_task()
            else:
                print("❌ Tiempo de espera agotado: El bot no pudo conectar.")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            await bot.close()
            print("🔌 Bot apagado.")

    asyncio.run(run_once())

