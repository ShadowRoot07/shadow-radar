import os
import asyncio
from google import genai

class AIHandler:
    def __init__(self):
        # Mantenemos el cliente
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded: 
            return "QUOTA_ERROR"

        try:
            # Volvemos a gemini-2.0-flash que es el nativo de esta librería
            # o usamos 'gemini-1.5-flash' sin prefijos raros.
            # Probemos con el 2.0 que es el que te dio el 429 (significa que sí lo encontró)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-2.0-flash", 
                contents=f"{prompt_intro}\n\nPost: {text[:1000]}"
            )
            
            if not response or not response.text:
                return "NO"
                
            return response.text.strip()

        except Exception as e:
            err_msg = str(e).upper()
            print(f"DEBUG AI: Error detectado -> {err_msg}")

            # Si el error es 429 o RESOURCE_EXHAUSTED, es cuota.
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            
            # Si vuelve a dar 404, imprimiremos más info para debuguear
            if "404" in err_msg:
                print("❌ El modelo no fue encontrado. Verifica el nombre del modelo.")
                return "NO"

            return "NO"

