import asyncio
from typing import AsyncIterator
from backend.scrapers.base import BaseScraper, ScrapedFile


class KunstderfugeScraper(BaseScraper):
    name = "kunstderfuge"
    INDEX_URL = "https://www.kunstderfuge.com/beethoven.htm"

    async def iter_files(self) -> AsyncIterator[ScrapedFile]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            midi_urls: list[str] = []

            def handle_response(response):
                url = response.url
                if url.lower().endswith((".mid", ".midi")):
                    midi_urls.append(url)

            page.on("response", handle_response)

            try:
                await page.goto(self.INDEX_URL, timeout=30000, wait_until="networkidle")
            except Exception:
                await browser.close()
                return

            # Click all download links to trigger the JS-rendered MIDI requests
            links = await page.query_selector_all("a[href*='midi'], a[href*='.mid']")
            for link in links[:50]:  # cap at 50 per run
                try:
                    await link.click()
                    await asyncio.sleep(0.3)
                except Exception:
                    continue

            await browser.close()

        for url in midi_urls:
            yield ScrapedFile(
                source_url=url,
                page_url=self.INDEX_URL,
                raw_filename=url.split("/")[-1],
                source_name=self.name,
            )
