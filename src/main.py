import os
import asyncio
import discord
from dotenv import load_dotenv

# Importamos tus clases personalizadas
from core.ai_handler import AIHandler
from modules.reddit_tracker import RedditScraper

load_dotenv()

# Prompts refinados para máxima relevancia
PROMPT_PSICO = "Analiza si este post muestra crisis emocional grave o riesgo. Resume en ESPAÑOL profesional. Si no es urgente, responde 'NO'."
PROMPT_TECH = "Si esta noticia es un hito importante en tecnología o IA (novedad real), resume en ESPAÑOL. Si no es relevante, responde 'NO'."

class ShadowRadar(discord.Client):
    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Canal no encontrado.")
            return

        ai = AIHandler()
        scraper = RedditScraper()
        
        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]

        print("🛰️ Iniciando patrullaje...")

        # Procesar Categoría Psicología
        for sub in subs_psico:
            # Usamos tu scraper de RSS que ya funciona
            posts, error = await scraper.get_latest_posts(sub)
            if error:
                print(f"⚠️ Error en r/{sub}: {error}")
                continue

            for p in posts:
                # Usamos tu AIHandler de core/ai_handler.py
                # Nota: Ajustado para usar el prompt de relevancia
                res = await ai.analyze_text(f"{p['title']}\n{p['text']}", PROMPT_PSICO)
                
                if res == "QUOTA_ERROR":
                    await channel.send("⚠️ **Aviso:** Cuota de Gemini agotada en este ciclo.")
                    return # Detenemos para no saturar

                if res and res.upper() != "NO":
                    await channel.send(f"🧠 **Radar Psico (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        # Procesar Categoría Tecnología
        for sub in subs_tech:
            if ai.quota_exceeded: break
            posts, _ = await scraper.get_latest_posts(sub)
            
            for p in posts:
                res = await ai.analyze_text(f"{p['title']}\n{p['text']}", PROMPT_TECH)
                
                if res == "QUOTA_ERROR": break
                
                if res and res.upper() != "NO":
                    await channel.send(f"💻 **Radar Tech (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        print("🏁 Ciclo completado.")

if __name__ == "__main__":
    intents = discord.Intents.default()
    bot = ShadowRadar(intents=intents)

    async def run():
        try:
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())
            
            # Esperar a que el bot esté listo
            for _ in range(15):
                if bot.is_ready(): break
                await asyncio.sleep(1)
            
            if bot.is_ready():
                await bot.background_task()
        finally:
            await bot.close()

    asyncio.run(run())

