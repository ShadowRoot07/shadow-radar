import os
import asyncio
import discord
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Configuración de Clientes
intents = discord.Intents.default()
intents.message_content = True
client_ai = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- PROMPTS ---
PROMPT_PSICOLOGIA = """
Analiza el siguiente post de Reddit. Si el autor muestra señales claras de crisis emocional, 
necesidad de terapia profesional o problemas psicológicos serios, responde con un resumen 
breve y profesional. Si es un problema menor, responde "NO".
Post: {texto}
"""

PROMPT_TECH = """
Analiza el siguiente post o noticia. Si es una noticia MUY destacable de tecnología, 
IA o programación (nuevos lenguajes, actualizaciones críticas, lanzamientos de impacto), 
responde con un resumen en ESPAÑOL. Si no es relevante, responde "NO".
Post: {texto}
"""

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar encendido como {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        prompt = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
        response = client_ai.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt.format(texto=texto)
        )
        return response.text.strip()

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Error: No se encontró el canal.")
            return

        # Aquí iría tu lógica de scraping de Reddit (PRAW o similar)
        # Ejemplo simulado de flujo:
        posts_psico = ["Post 1 sobre desahogo...", "Post 2..."]
        posts_tech = ["New release of Python 3.14", "Someone fixed a bug in a small library"]

        print("🔎 Escaneando para tu padre...")
        for p in posts_psico:
            res = await self.filtrar_con_ai(p, "psico")
            if res != "NO":
                await channel.send(f"⚠️ **Oportunidad Terapéutica:**\n{res}")

        print("🔎 Escaneando noticias Tech...")
        for t in posts_tech:
            res = await self.filtrar_con_ai(t, "tech")
            if res != "NO":
                await channel.send(f"🚀 **Radar Tech:**\n{res}")

# --- LÓGICA DE EJECUCIÓN ---
if __name__ == "__main__":
    bot = ShadowRadar(intents=intents)

    async def run_once():
        await bot.login(os.getenv("DISCORD_TOKEN"))
        asyncio.create_task(bot.connect())
        
        timeout = 0
        while not bot.is_ready() and timeout < 10:
            await asyncio.sleep(1)
            timeout += 1
            
        await bot.background_task()
        await bot.close()

    asyncio.run(run_once())

