import asyncio
from typing import AsyncIterator
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapedFile


class FreeMidiScraper(BaseScraper):
    name = "freemidi"
    BASE = "https://freemidi.org"

    async def iter_files(self) -> AsyncIterator[ScrapedFile]:
        page = 1
        while True:
            url = f"{self.BASE}/topmidi" if page == 1 else f"{self.BASE}/topmidi?page={page}"
            try:
                resp = await self.client.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception:
                break

            midi_links = [
                a for a in soup.find_all("a", href=True)
                if "/getter" in a["href"] or a["href"].lower().endswith(".mid")
            ]
            if not midi_links:
                break

            for a in midi_links:
                full_url = urljoin(self.BASE, a["href"])
                filename = a["href"].split("/")[-1] or a.get_text(strip=True)
                yield ScrapedFile(
                    source_url=full_url,
                    page_url=url,
                    raw_filename=filename if filename.endswith(".mid") else f"{filename}.mid",
                    source_name=self.name,
                    extra={"title": a.get_text(strip=True)},
                )

            page += 1
            await asyncio.sleep(self.rate_limit_delay)
