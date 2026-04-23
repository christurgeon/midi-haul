import asyncio
from typing import AsyncIterator
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapedFile


class VGMusicScraper(BaseScraper):
    name = "vgmusic"
    INDEX_URL = "https://www.vgmusic.com/music/"

    async def iter_files(self) -> AsyncIterator[ScrapedFile]:
        try:
            resp = await self.client.get(self.INDEX_URL, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            return

        # Find links to system/console sub-pages
        section_links = [
            urljoin(self.INDEX_URL, a["href"])
            for a in soup.find_all("a", href=True)
            if a["href"].endswith("/") and "music/" in a["href"]
        ]

        for section_url in section_links:
            async for sf in self._scrape_section(section_url):
                yield sf
            await asyncio.sleep(self.rate_limit_delay)

    async def _scrape_section(self, section_url: str) -> AsyncIterator[ScrapedFile]:
        try:
            resp = await self.client.get(section_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            return

        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if href.endswith(".mid") or href.endswith(".midi"):
                full_url = urljoin(section_url, a["href"])
                yield ScrapedFile(
                    source_url=full_url,
                    page_url=section_url,
                    raw_filename=a["href"].split("/")[-1],
                    source_name=self.name,
                    extra={"title": a.get_text(strip=True)},
                )
