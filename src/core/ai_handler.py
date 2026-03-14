import os
import asyncio
from google import genai

class AIHandler:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.quota_exceeded = False

    async def analyze_text(self, text, prompt_intro):
        if self.quota_exceeded: return "QUOTA_ERROR"
        
        try:
            # Pequeño respiro para la API
            await asyncio.sleep(2)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{prompt_intro}\n\nPost: {text[:1200]}"
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                self.quota_exceeded = True
                return "QUOTA_ERROR"
            return "NO"

