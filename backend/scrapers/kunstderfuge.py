import logging
from collections.abc import AsyncGenerator
from backend.scrapers.base import BaseScraper, ScrapedFile

logger = logging.getLogger(__name__)


class KunstderfugeScraper(BaseScraper):
    name = "kunstderfuge"
    DEFAULT_SEEDS = [
        "https://www.kunstderfuge.com/beethoven.htm",
        "https://www.kunstderfuge.com/bach.htm",
        "https://www.kunstderfuge.com/mozart.htm",
    ]

    def __init__(self, client, rate_limit_delay: float = 1.5, seed_urls: list[str] | None = None):
        super().__init__(client, rate_limit_delay)
        self.seed_urls = seed_urls or self.DEFAULT_SEEDS

    async def iter_files(self) -> AsyncGenerator[ScrapedFile, None]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for seed_url in self.seed_urls:
                async for sf in self._scrape_page(page, seed_url):
                    yield sf

            await browser.close()

    async def _scrape_page(self, page, seed_url: str) -> AsyncGenerator[ScrapedFile, None]:
        midi_urls: list[str] = []

        def handle_response(response):
            url = response.url
            if url.lower().endswith((".mid", ".midi")):
                midi_urls.append(url)

        page.on("response", handle_response)

        try:
            await page.goto(seed_url, timeout=30000, wait_until="networkidle")
        except Exception as e:
            logger.warning("Kunstderfuge %s: %s", seed_url, e)
            return

        # Click all download links to trigger the JS-rendered MIDI requests
        links = await page.query_selector_all("a[href*='midi'], a[href*='.mid']")
        for link in links[:50]:  # cap at 50 per run
            try:
                await link.click()
                await page.wait_for_timeout(int(self.rate_limit_delay * 1000))
            except Exception as e:
                logger.warning("Kunstderfuge %s: %s", seed_url, e)
                continue

        for url in midi_urls:
            yield ScrapedFile(
                source_url=url,
                page_url=seed_url,
                raw_filename=url.split("/")[-1],
                source_name=self.name,
            )
