import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.ai_handler import AIHandler

@pytest.mark.asyncio
async def test_ai_fallback_and_active_model():
    # 🟢 MOCK AL CLIENTE: Evitamos que Groq pida la key al inicializar
    with patch("src.core.ai_handler.Groq", return_value=MagicMock()):
        handler = AIHandler()
        
        mock_resp = AsyncMock()
        mock_resp.choices = [AsyncMock()]
        mock_resp.choices[0].message.content = "ANÁLISIS: DEPORTE"

        with patch("src.core.ai_handler.asyncio.to_thread") as mock_thread:
            mock_thread.side_effect = [
                Exception("Error 400: MODEL_DECOMMISSIONED"),
                mock_resp
            ]
            
            result = await handler.analyze_text("Test", "Prompt")
            assert result == "ANÁLISIS: DEPORTE"
            assert handler.active_model == "llama-3.1-8b-instant"

@pytest.mark.asyncio
async def test_quota_error_stop():
    # 🟢 MOCK AL CLIENTE
    with patch("src.core.ai_handler.Groq", return_value=MagicMock()):
        handler = AIHandler()
        
        with patch("src.core.ai_handler.asyncio.to_thread", side_effect=Exception("RATE_LIMIT_EXCEEDED")):
            result = await handler.analyze_text("Test", "Prompt")
            assert result == "QUOTA_ERROR"
            assert handler.quota_exceeded is True

