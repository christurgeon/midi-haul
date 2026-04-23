from backend.scrapers.base import BaseScraper, ScrapedFile
from backend.scrapers.bitmidi import BitMidiScraper
from backend.scrapers.vgmusic import VGMusicScraper
from backend.scrapers.freemidi import FreeMidiScraper
from backend.scrapers.kunstderfuge import KunstderfugeScraper
from backend.scrapers.crawler import GeneralCrawler

__all__ = [
    "BaseScraper",
    "ScrapedFile",
    "BitMidiScraper",
    "VGMusicScraper",
    "FreeMidiScraper",
    "KunstderfugeScraper",
    "GeneralCrawler",
]
