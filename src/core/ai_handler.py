import os
import asyncio
from google import genai

class AIHandler:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False
        # Lista refinada con versiones específicas y experimentales
        self.model_candidates = [
            "gemini-1.5-flash-latest",   # Forzar la última revisión estable
            "gemini-1.5-flash-002",      # Versión fija (a veces tiene cuota libre)
            "gemini-1.5-pro-latest",     # A veces el tier Pro tiene cuota cuando Flash no
            "gemini-2.0-flash-exp"       # Versión experimental de la 2.0
        ]
        self.active_model = None

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded:
            return "QUOTA_ERROR"

        models_to_try = [self.active_model] if self.active_model else self.model_candidates

        for model_name in models_to_try:
            if not model_name: continue
            
            try:
                # Reducimos aún más el texto para evitar bloqueos por tamaño de tokens
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model_name,
                    contents=f"{prompt_intro}\n\nContenido: {text[:700]}"
                )

                if response and hasattr(response, 'text') and response.text:
                    self.active_model = model_name
                    print(f"✅ Éxito con el modelo: {model_name}")
                    return response.text.strip()
                
            except Exception as e:
                err_msg = str(e).upper()
                
                # Si es cuota, probamos el siguiente modelo antes de rendirnos
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"⚠️ Cuota saturada para {model_name}, intentando siguiente...")
                    continue
                
                if "404" in err_msg or "NOT_FOUND" in err_msg:
                    print(f"🔍 {model_name} no disponible.")
                    continue
                
                if "SAFETY" in err_msg:
                    return "NO"

        # Si agotamos todos los modelos y todos dieron 429
        self.quota_exceeded = True
        return "QUOTA_ERROR"

