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

# --- (Mantén los PROMPTS y la clase RedditScraper igual que antes) ---
# [Insertar aquí los Prompts y la clase RedditScraper del código anterior]

class ShadowRadar(discord.Client):
    quota_exceeded = False

    async def filtrar_con_ai(self, texto, tipo="psico"):
        if self.quota_exceeded: return "QUOTA_ERROR"
        texto_plano = re.sub(r'<[^>]+>', '', texto).strip()[:1500]
        prompt_base = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        try:
            await asyncio.sleep(2) 
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt_base.format(texto=texto_plano)
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel: return

        while True: # BUCLE INFINITO PARA RENDER
            print(f"🕒 Iniciando ciclo de patrullaje: {datetime.now()}")
            self.quota_exceeded = False # Reiniciamos cuota en cada ciclo
            
            await channel.send("🚀 **Shadow Radar:** Iniciando patrullaje programado (cada 30 min)...")

            subs_psico = ["desahogo", "psicologia", "ayuda"]
            subs_tech = ["programming", "technology", "python"]
            scraper = RedditScraper()

            for cat, subs, tipo in [("Psicología", subs_psico, "psico"), ("Tecnología", subs_tech, "tech")]:
                for sub in subs:
                    posts, _ = await scraper.get_latest_posts(sub)
                    for p in posts:
                        res = await self.filtrar_con_ai(f"{p['title']}\n{p['text']}", tipo)
                        if res == "QUOTA_ERROR":
                            await channel.send("⚠️ **Cuota Gemini agotada.** Esperando al siguiente ciclo...")
                            break 
                        if res and res.upper() != "NO":
                            emoji = "🧠" if tipo == "psico" else "💻"
                            await channel.send(f"{emoji} **Radar {cat} (r/{sub}):**\n> {res}\n🔗 {p['url']}")

            await channel.send("🏁 **Patrullaje completado.** Siguiente revisión en 30 minutos.")
            print("💤 Durmiendo por 30 minutos...")
            await asyncio.sleep(1800) # 30 minutos exactos

if __name__ == "__main__":
    bot = ShadowRadar(intents=discord.Intents.default())
    bot.run(os.getenv("DISCORD_TOKEN")) # En Render usamos .run() directamente

