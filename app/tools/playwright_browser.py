import asyncio

from app.core.security import URLGuard
from app.tools.extractor import extract_html


class PlaywrightBrowser:
    name = "playwright"

    def __init__(self, guard: URLGuard, settings):
        self.guard, self.settings = guard, settings

    async def retrieve(self, url: str, objective: str = ""):
        from playwright.async_api import async_playwright

        url = await self.guard.validate(url)
        async with asyncio.timeout(self.settings.request_timeout_s):
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--disable-quic"])
                try:
                    context = await browser.new_context(service_workers="block", accept_downloads=False)

                    async def route_request(route):
                        try:
                            await self.guard.validate(route.request.url)
                            if route.request.method != "GET" or route.request.resource_type in {"image", "media", "font"}:
                                await route.abort()
                            else:
                                await route.continue_()
                        except ValueError:
                            await route.abort()

                    await context.route("**/*", route_request)
                    page = await context.new_page()
                    page.set_default_timeout(self.settings.request_timeout_s * 1000)
                    await page.goto(url, wait_until="domcontentloaded")
                    try:
                        await page.wait_for_load_state("networkidle", timeout=1500)
                    except Exception:
                        pass
                    final_url = await self.guard.validate(page.url)
                    html = await page.content()
                    if len(html.encode()) > self.settings.max_response_bytes:
                        raise ValueError("Browser response exceeds byte budget")
                    return extract_html(html, final_url, self.name, self.settings.max_content_chars)
                finally:
                    await browser.close()
