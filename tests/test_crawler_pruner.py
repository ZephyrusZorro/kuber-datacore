"""
Tests for Crawl4AI-style DOM Pruning and Resilient Web Crawler.
"""

import pytest
from backend.dom_pruner import DOMPruningEngine
from backend.web_crawler import WebCrawlerEngine
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
    assert "NVIDIA" in res.title
    assert res.raw_html_length > 500
