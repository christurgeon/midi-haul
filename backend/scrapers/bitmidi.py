import asyncio
from typing import AsyncIterator
import httpx
from backend.scrapers.base import BaseScraper, ScrapedFile


class BitMidiScraper(BaseScraper):
    name = "bitmidi"
    BASE = "https://bitmidi.com"

    async def iter_files(self) -> AsyncIterator[ScrapedFile]:
        page = 1
        while True:
            try:
                resp = await self.client.get(
                    f"{self.BASE}/api/midi",
                    params={"page": page},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break

            items = data.get("data") or data.get("items") or []
            if not items:
                break

            for item in items:
                slug = item.get("slug") or item.get("id")
                filename = item.get("filename") or f"{slug}.mid"
                yield ScrapedFile(
                    source_url=f"{self.BASE}/uploads/{slug}.mid",
                    page_url=f"{self.BASE}/{slug}",
                    raw_filename=filename,
                    source_name=self.name,
                    extra={
                        "composer": item.get("artist") or item.get("composer"),
                        "genre": item.get("genre"),
                    },
                )

            page += 1
            await asyncio.sleep(self.rate_limit_delay)
