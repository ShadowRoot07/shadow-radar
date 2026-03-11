from google import genai
import os

class AIHandler:
    def __init__(self):
        # El nuevo SDK usa el cliente directamente
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    def analyze_lead(self, text):
        prompt = f"""
        Analiza el siguiente post de redes sociales y determina si la persona busca ayuda psicológica o expresa problemas de salud mental serios.
        
        Post: "{text}"
        
        Responde estrictamente en este formato JSON:
        {{
            "es_potencial": "SI/NO",
            "urgencia": 1-10,
            "resumen": "breve resumen de 10 palabras"
        }}
        """
        try:
            # Nueva forma de llamar a Gemini 1.5 Flash
            response = self.client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error en IA: {e}"

