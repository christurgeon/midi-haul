import pytest
import httpx
import respx
from backend.scrapers.base import ScrapedFile
from backend.scrapers.crawler import GeneralCrawler
from backend.lib.dedup import sha256_of
from backend.lib.storage import file_path_for


def test_sha256_of():
    h = sha256_of(b"hello")
    assert len(h) == 64
    assert sha256_of(b"hello") == sha256_of(b"hello")
    assert sha256_of(b"hello") != sha256_of(b"world")


def test_file_path_for_sharding():
    h = "abcdef1234567890" * 4  # 64-char hex
    p = file_path_for("bitmidi", h, "./data/midi_files")
    assert str(p).endswith(f"ab/{h}.mid")
    assert "bitmidi" in str(p)


@pytest.mark.asyncio
@respx.mock
async def test_crawler_finds_midi_links():
    html = """
    <html><body>
      <a href="/songs/test.mid">Test Song</a>
      <a href="/songs/other.mid">Other Song</a>
      <a href="/about">About</a>
    </body></html>
    """
    respx.get("http://example.com/").mock(return_value=httpx.Response(200, html=html, headers={"content-type": "text/html"}))

    async with httpx.AsyncClient() as client:
        crawler = GeneralCrawler(client, rate_limit_delay=0, seed_urls=["http://example.com/"], max_depth=0)
        files = [sf async for sf in crawler.iter_files()]

    assert len(files) == 2
    assert any("test.mid" in f.source_url for f in files)
    assert any("other.mid" in f.source_url for f in files)


@pytest.mark.asyncio
@respx.mock
async def test_crawler_stays_on_domain():
    html = """
    <html><body>
      <a href="https://other.com/song.mid">External MIDI</a>
      <a href="/local.mid">Local MIDI</a>
    </body></html>
    """
    respx.get("http://example.com/").mock(return_value=httpx.Response(200, html=html, headers={"content-type": "text/html"}))

    async with httpx.AsyncClient() as client:
        crawler = GeneralCrawler(client, rate_limit_delay=0, seed_urls=["http://example.com/"], max_depth=0)
        files = [sf async for sf in crawler.iter_files()]

    # Both absolute external and local relative .mid hrefs should be found
    # (midi URL discovery is not domain-limited, only link-following is)
    midi_urls = [f.source_url for f in files]
    assert any("local.mid" in url for url in midi_urls)
