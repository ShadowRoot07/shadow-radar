import discord
import os
import json
from discord.ext import tasks
from dotenv import load_dotenv
from core.ai_handler import AIHandler
from modules.reddit_tracker import RedditScraper

load_dotenv()

class ShadowRadar(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = AIHandler()
        self.scraper = RedditScraper()
        self.channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
        self.subreddits = ["desahogo", "psicologia", "Ayuda"]
        self.seen_posts = set()  # Para no repetir reportes

    async def setup_hook(self):
        self.background_task.start()

    async def on_ready(self):
        print(f'✅ Radar encendido como {self.user}')
        await channel.send("🚀 El Radar está online y buscando...")
        print(f'📡 Monitoreando: {", ".join(self.subreddits)}')

    @tasks.loop(minutes=30)
    async def background_task(self):
        print("🔎 Escaneando subreddits...")
        channel = self.get_channel(self.channel_id)
        if not channel:
            print("❌ Error: No se encontró el canal de Discord.")
            return

        for sub in self.subreddits:
            posts = await self.scraper.get_latest_posts(sub)
            
            for post in posts:
                # Evitar duplicados
                if post['url'] in self.seen_posts:
                    continue
                
                # Pedir a Gemini que analice el post
                raw_ai_response = self.ai.analyze_lead(f"Título: {post['title']}\nContenido: {post['text']}")
                
                try:
                    # Limpiamos la respuesta por si Gemini añade backticks de markdown
                    clean_json = raw_ai_response.replace("```json", "").replace("```", "").strip()
                    analysis = json.loads(clean_json)

                    if analysis.get("es_potencial") == "SI":
                        # Creamos una tarjeta (Embed) elegante para tu padre
                        urgencia = int(analysis.get("urgencia", 1))
                        color = discord.Color.red() if urgencia > 7 else discord.Color.gold()
                        
                        embed = discord.Embed(
                            title="🎯 Posible Paciente Encontrado",
                            description=analysis.get("resumen", "Sin resumen"),
                            color=color,
                            url=post['url']
                        )
                        embed.add_field(name="👤 Usuario", value=f"u/{post['author']}", inline=True)
                        embed.add_field(name="🚨 Urgencia", value=f"{urgencia}/10", inline=True)
                        embed.add_field(name="📍 Subreddit", value=f"r/{sub}", inline=True)
                        embed.set_footer(text="Haz clic en el título para ir al post y contactar por DM.")

                        await channel.send(embed=embed)
                        print(f"✨ Lead enviado: {post['author']}")
                
                except Exception as e:
                    print(f"⚠️ Error procesando post de {post['author']}: {e}")
                
                # Marcar como visto
                self.seen_posts.add(post['url'])
                
            # Un pequeño respiro entre subreddits para no saturar
            await asyncio.sleep(5)

# OJO: Necesitamos activar los intents para que el bot pueda leer y enviar
intents = discord.Intents.default()
intents.message_content = True 


# Cambia esto al final de tu archivo main.py
if __name__ == "__main__":
    import asyncio
    client = ShadowRadar(intents=intents)
    
    # Esta lógica es para que el bot corra una vez y se cierre (ideal para Actions)
    async def run_once():
        await client.login(os.getenv("DISCORD_TOKEN"))
        await client.on_ready()
        await client.background_task() # Ejecuta el escaneo
        await client.close()

    asyncio.run(run_once())

