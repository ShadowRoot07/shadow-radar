import os
import asyncio
import discord
from dotenv import load_dotenv

# Importamos tus clases
from core.ai_handler import AIHandler
from modules.reddit_tracker import RedditScraper

load_dotenv()

PROMPT_PSICO = "Analiza si este post muestra crisis emocional grave o riesgo. Resume en ESPAÑOL profesional. Si no es urgente, responde 'NO'."
PROMPT_TECH = "Si esta noticia es un hito importante en tecnología o IA, resume en ESPAÑOL. Si no es relevante, responde 'NO'."

class ShadowRadar(discord.Client):
    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Canal de Discord no encontrado.")
            return

        ai = AIHandler()
        scraper = RedditScraper()
        
        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]

        print("🛰️ Iniciando patrullaje...")

        # Categorías a procesar
        categorias = [
            (subs_psico, PROMPT_PSICO, "🧠 **Radar Psico**"),
            (subs_tech, PROMPT_TECH, "💻 **Radar Tech**")
        ]

        for subs, prompt, tag in categorias:
            for sub in subs:
                # Corregimos el desempaquetado de posts
                posts = await scraper.get_latest_posts(sub)
                
                # Si scraper devuelve [] o None, evitamos el crash
                if not posts:
                    continue

                for p in posts:
                    # En RedditScraper JSON, el post es un dict. 
                    # Extraemos título y texto según la estructura de Reddit
                    try:
                        data = p.get('data', {})
                        titulo = data.get('title', '')
                        texto = data.get('selftext', '')
                        url = f"https://reddit.com{data.get('permalink', '')}"
                        
                        res = await ai.analyze_text(f"{titulo}\n{texto}", prompt)
                        
                        if res == "QUOTA_ERROR":
                            await channel.send("⚠️ **Aviso:** Cuota de Gemini agotada.")
                            return

                        if res and res.upper() != "NO":
                            await channel.send(f"{tag} (r/{sub}):\n> {res}\n🔗 {url}")
                    except Exception as e:
                        print(f"Error procesando post: {e}")
                        continue

        print("🏁 Patrullaje finalizado con éxito.")

if __name__ == "__main__":
    intents = discord.Intents.default()
    bot = ShadowRadar(intents=intents)

    async def run():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            # Conexión asíncrona
            await bot.register_commands() if hasattr(bot, 'register_commands') else None
            
            # Usamos una tarea para no bloquear el login
            asyncio.create_task(bot.connect())
            
            # Esperar a que el bot esté listo
            for _ in range(15):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            
            if bot.is_ready():
                await bot.background_task()
            else:
                print("❌ El bot no pudo conectarse a Discord a tiempo.")
        finally:
            await bot.close()

    asyncio.run(run())

