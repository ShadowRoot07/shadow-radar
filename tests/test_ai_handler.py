import pytest
from unittest.mock import AsyncMock, patch
from src.core.ai_handler import AIHandler

@pytest.mark.asyncio
async def test_ai_fallback_and_active_model():
    handler = AIHandler()
    
    # Mock de respuesta exitosa
    mock_resp = AsyncMock()
    mock_resp.choices = [AsyncMock()]
    mock_resp.choices[0].message.content = "ANÁLISIS: DEPORTE"

    # Simulamos que el primer modelo falla con 400 y el segundo tiene éxito
    with patch("src.core.ai_handler.asyncio.to_thread") as mock_thread:
        mock_thread.side_effect = [
            Exception("Error 400: MODEL_DECOMMISSIONED"), # Falla el 70b
            mock_resp                                     # Éxito el 8b
        ]
        
        result = await handler.analyze_text("Test", "Prompt")
        
        assert result == "ANÁLISIS: DEPORTE"
        # Verificamos que ahora el modelo activo es el segundo de tu lista
        assert handler.active_model == "llama-3.1-8b-instant"

@pytest.mark.asyncio
async def test_quota_error_stop():
    handler = AIHandler()
    
    with patch("src.core.ai_handler.asyncio.to_thread", side_effect=Exception("RATE_LIMIT_EXCEEDED")):
        result = await handler.analyze_text("Test", "Prompt")
        assert result == "QUOTA_ERROR"
        assert handler.quota_exceeded is True

