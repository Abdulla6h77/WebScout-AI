import os

import httpx
import pytest

from app.core.config import Settings
from app.core.security import URLGuard
from app.tools.playwright_browser import PlaywrightBrowser
from app.tools.tinyfish import TinyFish

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.getenv("WEBSCOUT_LIVE_TESTS") != "1", reason="Explicit live opt-in required")]


async def test_real_browser_page():
    page = await PlaywrightBrowser(URLGuard(), Settings(request_timeout_s=20)).retrieve("https://example.com/")
    assert "Example Domain" in page.content
    assert page.provider == "playwright"


async def test_real_tinyfish_browser():
    settings = Settings(request_timeout_s=60)
    if not settings.key("tinyfish"):
        pytest.skip("TINYFISH_API_KEY missing")
    async with httpx.AsyncClient() as client:
        page = await TinyFish(client, URLGuard(), settings).browse("https://example.com/", "Read the page title and description")
    assert page.content and page.evidence_kind == "agent_output"
