import pytest
from src.core.ai_handler import AIHandler

@pytest.mark.asyncio
async def test_prompt_logic_specialized():
    """Prueba de caja negra para verificar si el modelo entiende las nuevas categorías"""
    ai = AIHandler()
    prompt = (
        "Analiza si este post es sobre ASILO, DEPORTE o VOCACIONAL. "
        "Si no, responde 'NO'."
    )
    
    # Solo ejecutar si hay API KEY disponible para evitar fallos en CI
    import os
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("No hay API KEY para test de integración real")

    casos = [
        ("Busco psicólogo para rendimiento en tenis", "DEPORTE"),
        ("No sé qué carrera estudiar, me gusta medicina", "VOCACIONAL"),
        ("Trámites de refugiado y apoyo emocional", "ASILO"),
        ("Vendo teclado gamer usado", "NO")
    ]

    for texto, esperado in casos:
        res = await ai.analyze_text(texto, prompt)
        if esperado == "NO":
            assert res.upper() == "NO"
        else:
            assert esperado in res.upper()

