import os
import asyncio
import discord
from dotenv import load_dotenv

# Importamos tus clases originales
from core.ai_handler import AIHandler
from modules.reddit_tracker import RedditScraper

load_dotenv()

PROMPT_PSICO = "Analiza si este post muestra crisis emocional grave o riesgo. Resume en ESPAÑOL profesional. Si no es urgente, responde 'NO'."
PROMPT_TECH = "Si esta noticia es un hito importante en tecnología o IA, resume en ESPAÑOL. Si no es relevante, responde 'NO'."

class ShadowRadar(discord.Client):
    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        ai = AIHandler()
        scraper = RedditScraper()
        
        # 1. Mensaje de Inicio
        await channel.send("🚀 **Shadow Radar:** Iniciando patrullaje preventivo...")

        subs_psico = ["desahogo", "psicologia", "ayuda"]
        subs_tech = ["programming", "technology", "python"]

        # Procesar Psicología
        for sub in subs_psico:
            # Volvemos al desempaquetado correcto (posts, error) del RSS
            posts, error = await scraper.get_latest_posts(sub)
            if error:
                print(f"⚠️ Error en r/{sub}: {error}")
                continue

            for p in posts:
                # p es un dict con 'title', 'text', 'url' (formato RSS)
                res = await ai.analyze_text(f"{p['title']}\n{p['text']}", PROMPT_PSICO)
                if res == "QUOTA_ERROR":
                    await channel.send("⚠️ **Fuera de Servicio:** Cuota de Gemini agotada (429).")
                    return
                if res and res.upper() != "NO":
                    await channel.send(f"🧠 **Radar Psico (r/{sub}):**\n> {res}\n🔗 {p['url']}")

        # Procesar Tecnología
        for sub in subs_tech:
            if ai.quota_exceeded: break
            posts, _ = await scraper.get_latest_posts(sub)
            if not posts: continue

            for p in posts:
                res = await ai

