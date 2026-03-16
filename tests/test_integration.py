import pytest
import os
from unittest.mock import MagicMock, patch
from src.core.ai_handler import AIHandler

@pytest.mark.asyncio
async def test_prompt_logic_specialized():
    # 🟢 Si no hay key real (como en CI), mockeamos para que no falle el init
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "gsk_test_key_123":
        with patch("src.core.ai_handler.Groq", return_value=MagicMock()):
            ai = AIHandler()
            # Aquí podrías saltar el test si quieres que solo sea real
            pytest.skip("Saltando lógica real por falta de API KEY válida")
    else:
        ai = AIHandler()
        # ... resto de tu lógica de integración real

