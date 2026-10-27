import asyncio
import time
from collections import OrderedDict

from app.core.security import in_scope


class RetrievalExecutor:
    def __init__(self, http, tinyfish=None, browser=None, settings=None):
        self.http, self.tinyfish, self.browser, self.settings = http, tinyfish, browser, settings
        self.semaphore = asyncio.Semaphore(settings.concurrency)
        self.cache = OrderedDict()

    async def retrieve(self, url, objective, browser_required=False, domains=None):
        async with self.semaphore:
            key = (url, browser_required)
            if self.settings.cache_ttl_s and key in self.cache:
                timestamp, page = self.cache[key]
                if time.monotonic() - timestamp < self.settings.cache_ttl_s:
                    return page.model_copy(deep=True)
            providers = []
            if self.tinyfish:
                if browser_required and self.settings.tinyfish_agent_enabled:
                    providers.append(("agent", self.tinyfish.browse))
                else:
                    providers.append(("fetch", self.tinyfish.retrieve))
            if browser_required and self.browser:
                providers.append(("browser", self.browser.retrieve))
            if not browser_required:
                providers.append(("http", self.http.retrieve))
                if self.browser:
                    providers.append(("browser", self.browser.retrieve))
            for kind, call in providers:
                try:
                    page = await asyncio.wait_for(call(url, objective), self.settings.request_timeout_s + 1.2)
                    if not in_scope(page.url, domains or []):
                        continue
                    if page.evidence_kind == "agent_output":
                        # Re-fetch independently. Never cite agent prose as verified page evidence.
                        for fetch in (self.tinyfish.retrieve, self.browser.retrieve if self.browser else self.http.retrieve):
                            try:
                                verified = await fetch(page.url, objective)
                                if verified.content.strip() and in_scope(verified.url, domains or []):
                                    verified.links.extend(page.links)
                                    page = verified
                                    break
                            except Exception:
                                continue
                    if page.evidence_kind != "page_text" or not page.content.strip():
                        continue
                    if self.settings.cache_ttl_s:
                        self.cache[key] = (time.monotonic(), page.model_copy(deep=True))
                        while len(self.cache) > self.settings.cache_entries:
                            self.cache.popitem(last=False)
                    return page
                except (ValueError, OSError, asyncio.TimeoutError):
                    continue
                except Exception:
                    # Provider details can include signed URLs or keys; do not expose exception bodies.
                    continue
            raise ValueError("All eligible retrieval providers failed")
