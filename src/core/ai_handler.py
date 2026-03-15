import os
import asyncio
from google import genai

class AIHandler:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False
        # Lista de modelos de mayor a menor probabilidad de éxito en tier free
        self.model_candidates = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-2.0-flash"
        ]
        self.active_model = None

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded:
            return "QUOTA_ERROR"

        # Si ya encontramos un modelo que funciona, usamos ese siempre
        models_to_try = [self.active_model] if self.active_model else self.model_candidates

        for model_name in models_to_try:
            if not model_name: continue
            
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model_name,
                    contents=f"{prompt_intro}\n\nPost: {text[:800]}"
                )

                if response and hasattr(response, 'text'):
                    # ¡Bingo! Este modelo funciona, lo guardamos como favorito
                    self.active_model = model_name
                    return response.text.strip()
                
            except Exception as e:
                err_msg = str(e).upper()
                
                # Si es cuota, paramos todo
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"🛑 Cuota agotada para {model_name}")
                    self.quota_exceeded = True
                    return "QUOTA_ERROR"
                
                # Si el modelo no existe (404), probamos el siguiente de la lista
                if "404" in err_msg or "NOT_FOUND" in err_msg:
                    print(f"🔍 Modelo {model_name} no disponible, probando siguiente...")
                    continue
                
                # Si es un error de seguridad, saltamos el post pero no el modelo
                if "SAFETY" in err_msg:
                    return "NO"

        return "NO"

