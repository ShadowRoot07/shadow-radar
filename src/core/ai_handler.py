import os
import asyncio
from groq import Groq

class AIHandler:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.quota_exceeded = False
        # Lista de modelos candidatos (de más moderno/eficiente a respaldo)
        self.model_candidates = [
            "llama-3.3-70b-versatile",   # El más potente actual
            "llama-3.1-8b-instant",      # El balanceado y rápido
            "mixtral-8x7b-32768",        # Respaldo sólido de Mistral
            "gemma2-9b-it"               # Opción ligera de Google en Groq
        ]
        self.active_model = None

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded:
            return "QUOTA_ERROR"

        # Si ya encontramos uno que sirve, empezamos por ese
        models_to_try = [self.active_model] if self.active_model else self.model_candidates

        for model_name in models_to_try:
            if not model_name: continue
            
            try:
                chat_completion = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"{prompt_intro}. RESPONDE EN ESPAÑOL. Si no es relevante, responde 'NO'."
                        },
                        {
                            "role": "user", 
                            "content": f"Post: {text[:1500]}"
                        }
                    ],
                    model=model_name,
                    temperature=0.5,
                )
                
                # Si llegamos aquí, el modelo funciona
                self.active_model = model_name
                return chat_completion.choices[0].message.content.strip()

            except Exception as e:
                err_msg = str(e).upper()
                print(f"🔍 Probando {model_name}... Error: {err_msg[:50]}")

                # Si es error de cuota (429), pausamos el bot
                if "429" in err_msg or "RATE_LIMIT" in err_msg:
                    self.quota_exceeded = True
                    return "QUOTA_ERROR"
                
                # Si el modelo no existe o está depreciado (400/404), seguimos al siguiente
                if "MODEL_DECOMMISSIONED" in err_msg or "NOT_FOUND" in err_msg or "400" in err_msg:
                    self.active_model = None # Reseteamos por si acaso
                    continue
                
                # Otros errores menores, devolvemos NO
                return "NO"

        return "NO"

