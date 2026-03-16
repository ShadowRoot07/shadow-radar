import pytest
from unittest.mock import AsyncMock, patch
from src.modules.reddit_tracker import RedditScraper

@pytest.mark.asyncio
async def test_get_latest_posts_xml_parsing():
    scraper = RedditScraper()
    
    # Simulamos un string RSS real que tu regex pueda leer
    # Usamos una fecha reciente para que pase el filtro de 40 minutos
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    
    mock_rss = f"""
    <feed>
        <entry>
            <title>Post de Prueba Asilo</title>
            <updated>{now_iso}</updated>
            <link href="https://www.reddit.com/r/psicologia/test"/>
            <content type="html">Necesito ayuda profesional</content>
        </entry>
    </feed>
    """
    
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_rss

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        posts, error = await scraper.get_latest_posts("psicologia")
        assert error is None
        assert len(posts) == 1
        assert posts[0]["title"] == "Post de Prueba Asilo"
        assert "reddit.com" in posts[0]["url"]

@pytest.mark.asyncio
async def test_get_latest_posts_expired():
    scraper = RedditScraper()
    # Fecha vieja (hace 2 horas) para probar el filtro de 40 mins
    mock_rss = """
    <entry>
        <updated>2024-01-01T00:00:00+00:00</updated>
    </entry>
    """
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_rss

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        posts, error = await scraper.get_latest_posts("psicologia")
        assert len(posts) == 0 # Debería ser filtrado por viejo

