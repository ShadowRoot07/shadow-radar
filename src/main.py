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
responde con un resumen en ESPAÑOL. Si el post original está en inglés, TRADÚCELO al español. 
Si no es relevante, responde "NO".
Post: {texto}
"""

class ShadowRadar(discord.Client):
    async def on_ready(self):
        print(f"✅ Radar encendido como {self.user}")

    async def filtrar_con_ai(self, texto, tipo="psico"):
        try:
            prompt = PROMPT_PSICOLOGIA if tipo == "psico" else PROMPT_TECH
            response = client_ai.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt.format(texto=texto)
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e).lower()
            # Manejo de límite de cuota (Rate Limit / 429)
            if "429" in error_str or "quota" in error_str:
                print("⚠️ Cuota de Gemini agotada.")
                return "LIMITE_ALCANZADO"
            else:
                print(f"❌ Error inesperado en la IA: {e}")
                return "NO"

    async def background_task(self):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        if not channel:
            print("❌ Error: No se encontró el canal.")
            return

        # Aquí asumo que ya tienes integrada tu lógica de PRAW/Reddit
        # Para el ejemplo, usaremos listas vacías o simuladas
        posts_psico = [] # Sustituir por la lógica de scraping
        posts_tech = []  # Sustituir por la lógica de scraping

        # --- SECCIÓN PSICOLOGÍA ---
        print("🔎 Escaneando para tu padre...")
        for p in posts_psico:
            res = await self.filtrar_con_ai(p, "psico")
            
            if res == "LIMITE_ALCANZADO":
                await channel.send("🛑 **Aviso:** Se ha agotado la cuota gratuita de Gemini por hoy. El Radar se detendrá.")
                return # Salida total de la tarea
                
            if res != "NO":
                await channel.send(f"⚠️ **Oportunidad Terapéutica:**\n{res}")

        # --- SECCIÓN TECH ---
        print("🔎 Escaneando noticias Tech...")
        for t in posts_tech:
            res = await self.filtrar_con_ai(t, "tech")
            
            if res == "LIMITE_ALCANZADO":
                await channel.send("🛑 **Aviso:** Se ha agotado la cuota gratuita de Gemini durante el escaneo Tech.")
                return
                
            if res != "NO":
                await channel.send(f"🚀 **Radar Tech:**\n{res}")

# --- LÓGICA DE EJECUCIÓN (CI/CD friendly) ---
if __name__ == "__main__":
    bot = ShadowRadar(intents=intents)

    async def run_once():
        try:
            # Login con timeout para evitar que GitHub Actions se quede colgado
            await bot.login(os.getenv("DISCORD_TOKEN"))
            asyncio.create_task(bot.connect())

            timeout = 0
            while not bot.is_ready() and timeout < 15:
                await asyncio.sleep(1)
                timeout += 1

            if bot.is_ready():
                await bot.background_task()
            else:
                print("❌ No se pudo conectar a Discord en el tiempo previsto.")
                
        finally:
            await bot.close()
            print("🔌 Radar desconectado.")

    asyncio.run(run_once())

