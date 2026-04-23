import asyncio
import logging
from collections.abc import AsyncGenerator
from backend.scrapers.base import BaseScraper, ScrapedFile

logger = logging.getLogger(__name__)


class BitMidiScraper(BaseScraper):
    name = "bitmidi"
    BASE = "https://bitmidi.com"

    async def iter_files(self) -> AsyncGenerator[ScrapedFile, None]:
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
            except Exception as e:
                logger.warning("BitMidi page %d failed: %s", page, e)
                break

            items = data.get("data") or data.get("items") or []
            if not items:
                break

            for item in items:
                slug = item.get("slug") or item.get("id")
                filename = item.get("filename") or f"{slug}.mid"
                download_url = (
                    item.get("download_url")
                    or item.get("url")
                    or f"{self.BASE}/uploads/{slug}.mid"
                )
                yield ScrapedFile(
                    source_url=download_url,
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
