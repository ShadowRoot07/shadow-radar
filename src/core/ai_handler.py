import os
import asyncio
from google import genai

class AIHandler:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded:
            return "QUOTA_ERROR"

        try:
            # Usamos gemini-1.5-flash-8b: es más rápido y tiene cuotas separadas.
            # Reducimos un poco el texto (800) para asegurar que no saturemos tokens.
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-1.5-flash-8b",
                contents=f"{prompt_intro}\n\nPost: {text[:800]}"
            )

            # Verificamos que la respuesta tenga contenido antes de procesar
            if not response or not hasattr(response, 'text') or not response.text:
                return "NO"

            return response.text.strip()

        except Exception as e:
            err_msg = str(e).upper()
            print(f"DEBUG AI: Error detectado -> {err_msg}")

            # Capturamos 429 (Límite por minuto) y RESOURCE_EXHAUSTED (Límite diario)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            
            # Si el filtro de seguridad de Google bloquea el post
            if "SAFETY" in err_msg or "CANDIDATE" in err_msg:
                return "NO"

            return "NO"

