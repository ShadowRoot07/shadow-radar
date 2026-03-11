import google.generativeai as genai
import os

class AIHandler:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

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
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error en IA: {e}"

