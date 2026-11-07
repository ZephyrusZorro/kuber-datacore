"""
Tests for Crawl4AI-style DOM Pruning and Resilient Web Crawler.
"""

import gzip

import anyio
import httpx
import pytest
from backend.dom_pruner import DOMPruningEngine
from backend.web_crawler import CrawlFetchError, WebCrawlerEngine
from backend.models import FilterStrategy, CrawlRequest


@pytest.fixture
def pruner():
    return DOMPruningEngine()


@pytest.fixture
def crawler():
    return WebCrawlerEngine()


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Semiconductor Report</title></head>
<body>
    <script>var tracker = 123;</script>
    <div class="ad-banner">Buy crypto now!</div>
    <nav><a href="/1">1</a><a href="/2">2</a><a href="/3">3</a><a href="/4">4</a><a href="/5">5</a></nav>
    <main>
        <h1>Nvidia & TSMC Strategic AI Partnership</h1>
        <p>NVIDIA Corporation pioneered accelerated computing to tackle complex problems.</p>
        <p>TSMC manufactures advanced 4N lithography chips for Nvidia Hopper architectures.</p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Revenue</td><td>60.9B</td></tr>
            <tr><td>Gross Margin</td><td>72.7%</td></tr>
        </table>
    </main>
    <footer><div class="disclaimer-footer">Copyright 2024</div></footer>
</body>
</html>
"""


def test_dom_pruner_strips_boilerplate(pruner):
    res = pruner.prune_and_convert(SAMPLE_HTML, strategy=FilterStrategy.PRUNING_LXML)
    assert "Buy crypto now" not in res.markdown_content
    assert "tracker" not in res.markdown_content
    assert "# Nvidia & TSMC Strategic AI Partnership" in res.markdown_content
    assert "| Revenue | 60.9B |" in res.markdown_content
    assert res.compression_ratio_pct > 0.0


def test_dom_pruner_bm25_filtering(pruner):
    res = pruner.prune_and_convert(
        SAMPLE_HTML,
        strategy=FilterStrategy.BM25_RELEVANCE,
        query_context="TSMC advanced lithography manufacturing"
    )
    assert "TSMC manufactures" in res.markdown_content


def test_dom_pruner_semantic_chunking(pruner):
    res = pruner.prune_and_convert(
        SAMPLE_HTML,
        strategy=FilterStrategy.TOKEN_WINDOW_CHUNK,
        chunk_size_words=10,
        chunk_overlap_words=2
    )
    assert len(res.chunks) >= 1
    assert res.chunks[0].word_count > 0


@pytest.mark.anyio
async def test_crawler_mock_fetch(crawler):
    req = CrawlRequest(url="https://sec.gov/edgar/nvda-10k")
    res = await crawler.crawl(req)
    assert res.status_code == 200
    assert res.source == "fixture"
    assert "NVIDIA" in res.title
    assert res.raw_html_length > 500

@pytest.mark.anyio
async def test_unavailable_custom_url_fails_without_a_fixture():
    async def unavailable(request):
        raise httpx.ConnectError("Unavailable", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(unavailable)) as client:
        with pytest.raises(CrawlFetchError, match="Could not reach"):
            await WebCrawlerEngine(client).crawl(CrawlRequest(url="https://example.invalid/report"))


def test_pruner_handles_nested_boilerplate(pruner):
    result = pruner.prune_and_convert(
        '<div class="ad-banner"><div><span>Sponsored</span></div></div>'
        '<main><p>Research document</p></main>'
    )
    assert result.markdown_content == "Research document"


def test_prune_request_rejects_a_chunk_window_that_cannot_advance():
    from pydantic import ValidationError
    from backend.models import DOMPruneRequest

    with pytest.raises(ValidationError, match="overlap"):
        DOMPruneRequest(
            raw_html="<p>Research document</p>",
            strategy=FilterStrategy.TOKEN_WINDOW_CHUNK,
            chunk_size_words=10,
            chunk_overlap_words=10,
        )

@pytest.mark.anyio
async def test_web_fetch_keeps_document_when_a_link_is_malformed():
    async def fetch(request):
        return httpx.Response(
            200, stream=httpx.ByteStream(b'<main>Actual report</main><a href="http://[">Broken</a><a href="/filing">Filing</a>')
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch)) as client:
        result = await WebCrawlerEngine(client).crawl(CrawlRequest(url="https://example.invalid/report"))
    assert result.source == "web"
    assert "Actual report" in result.raw_html
    assert result.extracted_links == ["https://example.invalid/filing"]


@pytest.mark.anyio
@pytest.mark.parametrize("compressed", [False, True])
async def test_crawler_rejects_oversized_documents(compressed):
    async def fetch(request):
        body = b"x" * 4096
        if compressed:
            return httpx.Response(200, stream=httpx.ByteStream(gzip.compress(body)), headers={"Content-Encoding": "gzip"})
        return httpx.Response(200, stream=httpx.ByteStream(body))

    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch)) as client:
        crawler = WebCrawlerEngine(client)
        crawler.MAX_DOCUMENT_BYTES = 128
        with pytest.raises(CrawlFetchError, match="download limit"):
            await crawler.crawl(CrawlRequest(url="https://example.invalid/report"))


@pytest.mark.anyio
async def test_crawler_enforces_a_total_download_deadline():
    class SlowStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(10):
                await anyio.sleep(0.05)
                yield b"x"

    async def fetch(request):
        return httpx.Response(200, stream=SlowStream())

    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch)) as client:
        with pytest.raises(CrawlFetchError, match="timed out"):
            await WebCrawlerEngine(client).crawl(CrawlRequest(url="https://example.invalid/report", timeout_seconds=0.15))

@pytest.mark.anyio
async def test_crawler_does_not_buffer_redirect_bodies():
    class UnreadableRedirect(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError("Redirect body must not be read")
            yield b""

    async def fetch(request):
        if request.url.path == "/report":
            return httpx.Response(302, headers={"Location": "/final"}, stream=UnreadableRedirect())
        return httpx.Response(200, stream=httpx.ByteStream(b"<main>Final report</main>"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch), follow_redirects=True) as client:
        result = await WebCrawlerEngine(client).crawl(CrawlRequest(url="https://example.invalid/report"))
    assert result.url == "https://example.invalid/final"
    assert "Final report" in result.raw_html


@pytest.mark.anyio
async def test_crawler_reads_gzip_and_preserves_charset():
    async def fetch(request):
        assert request.headers["Accept-Encoding"] == "gzip, identity"
        compressed = gzip.compress(b"<main>Caf\xe9</main>")
        return httpx.Response(200, headers={
            "Content-Encoding": "gzip",
            "Content-Type": "text/html; charset=iso-8859-1",
        }, stream=httpx.ByteStream(compressed))

    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch)) as client:
        document = await WebCrawlerEngine(client).crawl(CrawlRequest(url="https://example.invalid/report"))
    assert document.raw_html == "<main>Caf\xe9</main>"

@pytest.mark.anyio
async def test_crawler_retains_cookies_only_within_a_redirect_chain():
    async def fetch(request):
        if request.url.path == "/report":
            assert "cookie" not in request.headers
            return httpx.Response(302, headers={
                "Location": "/final",
                "Set-Cookie": "visited=1; Path=/",
            }, stream=httpx.ByteStream(b""))
        if request.headers.get("cookie") != "visited=1":
            return httpx.Response(403, stream=httpx.ByteStream(b""))
        return httpx.Response(200, stream=httpx.ByteStream(b"<main>Final report</main>"))

    from http.cookiejar import CookieJar, DefaultCookiePolicy

    cookies = CookieJar(policy=DefaultCookiePolicy(allowed_domains=()))
    async with httpx.AsyncClient(transport=httpx.MockTransport(fetch), cookies=cookies) as client:
        crawler = WebCrawlerEngine(client)
        request = CrawlRequest(url="https://example.invalid/report")
        for _ in range(2):
            assert (await crawler.crawl(request)).status_code == 200
        assert not client.cookies
