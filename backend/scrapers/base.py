import logging
import httpx
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScrapedFile:
    source_url: str        # direct URL to the .mid file
    page_url: str          # page where it was found
    raw_filename: str      # filename from URL or content-disposition
    source_name: str       # "bitmidi", "vgmusic", "crawler", etc.
    extra: dict = field(default_factory=dict)  # scraper-specific bonus metadata


class BaseScraper(ABC):
    name: str

    def __init__(self, client: httpx.AsyncClient, rate_limit_delay: float = 1.5):
        self.client = client
        self.rate_limit_delay = rate_limit_delay

    @abstractmethod
    async def iter_files(self) -> AsyncGenerator[ScrapedFile, None]:
        """Yields ScrapedFile for every MIDI found on this source."""
        yield  # required for async generator protocol
        raise NotImplementedError

    async def download(self, sf: ScrapedFile) -> bytes:
        resp = await self.client.get(sf.source_url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.content
