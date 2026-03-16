import os
import asyncio
import discord
from dotenv import load_dotenv
from core.ai_handler import AIHandler
from modules.reddit_tracker import RedditScraper

load_dotenv()

class ShadowRadar(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scanning = False

    async def on_ready(self):
        if self.scanning: return
        self.scanning = True

        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            await self.close()
            return

        try:
            ai = AIHandler()
            scraper = RedditScraper()

            await channel.send("🚀 **Shadow Radar:** Iniciando patrullaje especializado...")

            # Subreddits estratégicos para las nuevas categorías
            subs_psico = ["desahogo", "psicologia", "ayuda", "orientacionvocal", "DerechoGenial"]
            subs_tech = ["programming", "technology", "python"]

            # Prompt refinado con las nuevas categorías integradas
            psico_prompt = (
                "Analiza si este post encaja en una de estas categorías críticas:\n"
                "1. CRISIS: Riesgo emocional grave o urgencia.\n"
                "2. ASILO: Extranjeros que necesitan apoyo psicológico para trámites de asilo o migración.\n"
                "3. DEPORTE: Atletas que buscan mejorar rendimiento mediante psicología deportiva.\n"
                "4. VOCACIONAL: Personas que requieren orientación profesional o académica.\n\n"
                "Si detectas alguna, resume en ESPAÑOL indicando la categoría y por qué es relevante. "
                "Si no es ninguna de estas, responde únicamente 'NO'."
            )

            all_subs = [
                (subs_psico, psico_prompt, "🧠 Radar Psico Especializado"),
                (subs_tech, "Si esta noticia es un hito importante en tecnología o IA, resume en ESPAÑOL. Si no es relevante, responde 'NO'.", "💻 Radar Tech")
            ]

            for group, prompt, tag in all_subs:
                for sub in group:
                    print(f"🛰️ Patrullando r/{sub}...")
                    posts, error = await scraper.get_latest_posts(sub)

                    if error:
                        print(f"⚠️ Error en r/{sub}: {error}")
                        continue

                    for p in posts[:3]:
                        # ⏱️ SLEEP ULTRA-SAFE: 10 segundos para respetar Groq
                        await asyncio.sleep(10)

                        res = await ai.analyze_text(f"{p['title']}\n{p['text']}", prompt)

                        if res == "QUOTA_ERROR":
                            print("⏳ Cuota saturada en Groq. Reintentando en 30s...")
                            await asyncio.sleep(30)
                            res = await ai.analyze_text(f"{p['title']}\n{p['text']}", prompt)

                            if res == "QUOTA_ERROR":
                                await channel.send("🛑 **Pausa Forzada:** Límite de Groq alcanzado.")
                                await self.close()
                                return

                        if res and res.upper() != "NO":
                            await channel.send(f"{tag} (r/{sub}):\n> {res}\n🔗 {p['url']}")

            await channel.send("🏁 **Patrullaje finalizado con éxito.**")

        except Exception as e:
            print(f"💥 Error crítico: {e}")
        finally:
            await self.close()

if __name__ == "__main__":
    intents = discord.Intents.default()
    bot = ShadowRadar(intents=intents)
    async def main():
        async with bot:
            await bot.start(os.getenv("DISCORD_TOKEN"))
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

