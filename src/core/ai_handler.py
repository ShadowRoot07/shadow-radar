import os
import asyncio
from groq import Groq

class AIHandler:
    def __init__(self):
        # Inicializamos el cliente de Groq
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.quota_exceeded = False

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded:
            return "QUOTA_ERROR"

        try:
            # Usamos Llama 3 8B, que es perfecto para resúmenes rápidos y gratuito
            # Usamos to_thread para no bloquear el bot de Discord
            chat_completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[
                    {
                        "role": "system", 
                        "content": f"{prompt_intro}. RESPONDE SIEMPRE EN ESPAÑOL. Si el contenido no es relevante, responde únicamente 'NO'."
                    },
                    {
                        "role": "user", 
                        "content": f"Analiza este post de Reddit: {text[:1500]}"
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.5, # Un poco de creatividad pero controlado
            )
            
            result = chat_completion.choices[0].message.content.strip()
            return result

        except Exception as e:
            err_msg = str(e).upper()
            print(f"DEBUG AI (Groq): {err_msg}")
            
            # Groq también tiene límites (Rate Limits), los capturamos aquí
            if "429" in err_msg or "RATE_LIMIT" in err_msg:
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            
            return "NO"

