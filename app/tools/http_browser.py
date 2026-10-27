from urllib.parse import urljoin

import httpx

from app.core.security import URLGuard
from app.tools.extractor import extract_html


class HTTPBrowser:
    name = "httpx"

    def __init__(self, client: httpx.AsyncClient, guard: URLGuard, settings):
        self.client, self.guard, self.settings = client, guard, settings

    async def retrieve(self, url: str, objective: str = ""):
        for _ in range(6):
            url, address = await self.guard.resolve(url)
            parsed = httpx.URL(url)
            # Connect to the validated IP, retaining Host and TLS SNI: no second DNS lookup.
            pinned_url = parsed.copy_with(host=address)
            async with self.client.stream("GET", pinned_url, follow_redirects=False,
                                          headers={"Host": parsed.netloc.decode()},
                                          extensions={"sni_hostname": parsed.host},
                                          timeout=self.settings.request_timeout_s) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                if not any(x in response.headers.get("content-type", "") for x in ("text/", "html", "json")):
                    raise ValueError("Unsupported response content type")
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.settings.max_response_bytes:
                        raise ValueError("Response exceeds byte budget")
                    chunks.append(chunk)
                return extract_html(b"".join(chunks).decode("utf-8", errors="replace"),
                                    url, self.name, self.settings.max_content_chars)
        raise ValueError("Redirect limit exceeded")
