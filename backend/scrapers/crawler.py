import asyncio
from typing import AsyncIterator
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapedFile


class GeneralCrawler(BaseScraper):
    name = "crawler"

    def __init__(self, client, rate_limit_delay: float = 1.5, seed_urls: list[str] | None = None, max_depth: int = 3):
        super().__init__(client, rate_limit_delay)
        self.seed_urls = seed_urls or []
        self.max_depth = max_depth

    async def iter_files(self) -> AsyncIterator[ScrapedFile]:
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(url, 0) for url in self.seed_urls]

        while queue:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            links, midi_urls = await self._fetch_and_parse(url)

            for midi_url in midi_urls:
                yield ScrapedFile(
                    source_url=midi_url,
                    page_url=url,
                    raw_filename=midi_url.split("/")[-1].split("?")[0],
                    source_name=self.name,
                )

            if depth < self.max_depth:
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

            await asyncio.sleep(self.rate_limit_delay)

    async def _fetch_and_parse(self, url: str) -> tuple[list[str], list[str]]:
        try:
            resp = await self.client.get(url, timeout=10, follow_redirects=True)
            if "text/html" not in resp.headers.get("content-type", ""):
                return [], []
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            return [], []

        base_domain = urlparse(url).netloc

        midi_urls = [
            urljoin(url, a["href"])
            for a in soup.find_all("a", href=True)
            if a["href"].lower().split("?")[0].endswith((".mid", ".midi"))
        ]

        # Stay on same domain for link following
        links = [
            urljoin(url, a["href"])
            for a in soup.find_all("a", href=True)
            if urlparse(urljoin(url, a["href"])).netloc == base_domain
            and a["href"] not in ("#", "/", "")
            and not a["href"].startswith("mailto:")
        ]

        return links, midi_urls
