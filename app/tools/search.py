class SearchDiscovery:
    """Discovery is separate from browsing; no undocumented search-engine scraping."""

    def __init__(self, tinyfish=None):
        self.tinyfish = tinyfish

    async def discover(self, query, domains, page=0):
        if self.tinyfish is None:
            return []
        return await self.tinyfish.search(query, domains, page)
