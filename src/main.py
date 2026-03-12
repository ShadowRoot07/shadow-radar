import os
import asyncio
import discord
import httpx
import random
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- PROMPTS DE PRUEBA (SIN FILTROS) ---
PROMPT_PSICOLOGIA = """
Resume este post de Reddit en una sola frase breve y descriptiva en ESPAÑOL:
{texto}
"""

PROMPT_TECH = """
Resume este post de tecnología en una sola frase breve y descriptiva en ESPAÑOL:
{texto}
"""

class RedditScraper:
    def __init__(self):
        self.url_template = "https://www.reddit.com/r/{}/new.rss"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
        }

    async def get_latest_posts(self, subreddit):
        await asyncio.sleep(random.uniform(2.0, 4.0))
        url = self.url_template.format(subreddit.lower())
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    xml_content = response.text
                    # Extracción de datos con Regex
                    titles = re.findall(r'<title>(.*?)</title>', xml_content)
                    titles = titles[1:] if len(titles) > 1 else titles
                    links = re.findall(r'<link href="(https://www.reddit.com/r/[^"]+)"', xml_content)
                    contents = re.findall(r'<content type="html">(.*?)</content>', xml_content)
                    
                    results = []
                    # Aumentamos a 10 para asegurar que pesque algo
                    for i in range(min(len(titles), 10)):
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
        # Limpieza básica
        texto_plano = re.sub(r'<[^>]+>', '', texto)
        texto_plano = texto_plano.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        texto_plano = texto_plano.strip()[:1500]
        
        if not texto_plano: return "Post sin contenido legible."
        
        prompt_base = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        try:
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt_base.format(texto=texto_plano)
            )
            return response.text.strip()
        except Exception as e:
            return f"Error procesando con AI: {str(e)}"

    async def background_task(self):
        channel_id = os.getenv("DISCORD_CHANNEL_ID")
        channel = self.get_channel(int(channel_id))
        if not channel:
            print(f"❌ Error: Canal {channel_id} no encontrado.")
            return

        await channel.send("🧪 **MODO PRUEBA:** Iniciando extracción directa de Reddit...")

        subs_psico = ["desahogo", "psicologia"]
        subs_tech = ["programming", "technology", "python"]
        scraper = RedditScraper()

        print("🔎 Iniciando escaneo...")
        
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

                if not posts:
                    print(f"LOG: No se encontraron posts en r/{sub}")
                    continue

                for p in posts:
                    # En modo prueba, procesamos TODO lo que venga
                    analisis = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo_ai)
                    
                    emoji = "🧪" 
                    mensaje = (
                        f"{emoji} **Dato extraído de r/{sub}:**\n"
                        f"> {analisis}\n"
                        f"🔗 [Link al post]({p['url']})"
                    )
                    await channel.send(mensaje)
                    await asyncio.sleep(0.5)

        print("💤 Tarea finalizada.")
        await channel.send("🏁 **Modo Prueba Finalizado.**")

if __name__ == "__main__":
    intents = discord.Intents.default()
    bot = ShadowRadar(intents=intents)

    async def run_once():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())
            
            for _ in range(20):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            
            if bot.is_ready():
                await bot.background_task()
            else:
                print("❌ Tiempo de espera agotado.")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await bot.close()
            print("🔌 Bot apagado.")

    asyncio.run(run_once())

