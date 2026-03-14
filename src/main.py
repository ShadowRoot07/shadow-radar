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

            await channel.send("🚀 **Shadow Radar:** Iniciando patrullaje...")

            subs_psico = ["desahogo", "psicologia", "ayuda"]
            subs_tech = ["programming", "technology", "python"]

            all_subs = [
                (subs_psico, "Analiza si este post muestra crisis emocional grave o riesgo. Resume en ESPAÑOL profesional. Si no es urgente, responde 'NO'.", "🧠 Radar Psico"),
                (subs_tech, "Si esta noticia es un hito importante en tecnología o IA, resume en ESPAÑOL. Si no es relevante, responde 'NO'.", "💻 Radar Tech")
            ]

            for group, prompt, tag in all_subs:
                for sub in group:
                    print(f"🛰️ Patrullando r/{sub}...")
                    posts, error = await scraper.get_latest_posts(sub)
                    
                    if error:
                        print(f"⚠️ Error en r/{sub}: {error}")
                        continue

                    # Solo procesamos los 3 posts más recientes para cuidar la cuota
                    for p in posts[:3]:
                        # ⏱️ SLEEP ULTRA-SAFE: 10 segundos entre posts
                        await asyncio.sleep(10)

                        res = await ai.analyze_text(f"{p['title']}\n{p['text']}", prompt)
                        
                        if res == "QUOTA_ERROR":
                            # Si da error, esperamos 30 segundos y reintentamos UNA vez
                            print("⏳ Cuota saturada. Reintentando en 30s...")
                            await asyncio.sleep(30)
                            res = await ai.analyze_text(f"{p['title']}\n{p['text']}", prompt)
                            
                            if res == "QUOTA_ERROR":
                                await channel.send("🛑 **Pausa Forzada:** Cuota diaria de Gemini agotada.")
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

