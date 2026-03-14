import os
import asyncio
from google import genai
from google.genai import errors

class AIHandler:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False

    async def analyze_text(self, text, prompt_intro):
        # Si ya sabemos que la cuota murió, ni siquiera intentamos
        if self.quota_exceeded: 
            return "QUOTA_ERROR"

        try:
            # Llamada síncrona envuelta en thread para no bloquear el loop de discord
            # Usamos 1.5-flash para mayor estabilidad en el tier free
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-1.5-flash", 
                contents=f"{prompt_intro}\n\nPost: {text[:1000]}"
            )
            
            if not response or not response.text:
                return "NO"
                
            return response.text.strip()

        except Exception as e:
            err_msg = str(e).upper()
            print(f"DEBUG AI: Error detectado -> {err_msg}") # Para que lo veas en los logs de GH

            # Capturamos todas las variantes de exceso de recursos
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "QUOTA" in err_msg:
                print("🚨 CUOTA AGOTADA 🚨")
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            
            # Si el error es por seguridad (Hate speech, etc) Reddit suele dispararlo
            if "SAFETY" in err_msg:
                return "NO"

            return "NO"

