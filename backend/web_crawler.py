"""
Kuber Data Core (कुबेर) — Resilient Async Web Crawler
HTTP fetching and bundled financial documents.
"""

import time
import re
import urllib.parse
from typing import List
import httpx

from backend.models import CrawlRequest, CrawlResponse


class CrawlFetchError(RuntimeError):
    pass


class WebCrawlerEngine:
    """Fetch HTML and discover links, with bundled documents for offline demos."""

    USER_AGENTS = {
        "desktop_chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "data_bot": "KuberDataCore/1.0 (+https://github.com/ZephyrusZorro/kuber-datacore; Research & Financial Analysis)",
        "financial_crawler": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    }

    # Rich pre-loaded financial web mocks for guaranteed zero-dependency offline resilience
    MOCK_DOMAINS = {
        "sec.gov/edgar/nvda-10k": """
        <!DOCTYPE html>
        <html>
        <head><title>NVIDIA CORP - Form 10-K Annual Report (CIK: 0001045810)</title></head>
        <body>
            <header><div class="ad-banner">SEC Public Disclosure System</div><nav><a href="/home">Home</a> | <a href="/search">Search</a></nav></header>
            <main>
                <h1>NVIDIA CORPORATION — UNITED STATES SECURITIES AND EXCHANGE COMMISSION</h1>
                <p><strong>FORM 10-K ANNUAL REPORT</strong> for the Fiscal Year Ended January 28, 2024</p>
                <p>Commission File Number: 000-23985 | CIK: 0001045810</p>
                
                <h2>ITEM 1. BUSINESS OVERVIEW</h2>
                <p>NVIDIA pioneered accelerated computing to tackle challenges that no one else can solve. Our work in AI and digital twins is transforming the world's largest industries. We specialize in GPUs, Data Center architectures, and the CUDA software computing platform.</p>
                <p>Our Data Center revenue grew to $47.5 billion, driven by compute platforms for large language models, recommendation engines, and generative AI applications. Major cloud providers including Microsoft Azure, Amazon Web Services, Alphabet Google Cloud, and Oracle Cloud deployed our H100 and Hopper Tensor Core GPUs.</p>
                
                <h2>ITEM 1A. SUPPLY CHAIN & RISK FACTORS</h2>
                <p>We rely on single-source and critical third-party wafer foundries, primarily Taiwan Semiconductor Manufacturing Company (TSMC), to manufacture our advanced lithography semiconductor chips. Any disruption in Taiwan, seismic events, or geopolitical friction would severely constrain our GPU supply. Furthermore, we depend on ASML for extreme ultraviolet (EUV) photolithography technology used across our supply chain.</p>
                
                <h2>ITEM 7. CONSOLIDATED BALANCE SHEET & FINANCIAL SUMMARY</h2>
                <table>
                    <tr><th>Financial Metric</th><th>FY 2024 (Billions USD)</th><th>FY 2023 (Billions USD)</th></tr>
                    <tr><td>Total Revenue</td><td>60.92</td><td>26.97</td></tr>
                    <tr><td>Gross Profit</td><td>44.30</td><td>15.36</td></tr>
                    <tr><td>Operating Income (EBIT)</td><td>32.97</td><td>4.22</td></tr>
                    <tr><td>Net Income</td><td>29.76</td><td>4.37</td></tr>
                    <tr><td>Total Assets</td><td>65.73</td><td>41.18</td></tr>
                    <tr><td>Total Liabilities</td><td>22.75</td><td>19.08</td></tr>
                    <tr><td>Current Assets</td><td>44.34</td><td>23.07</td></tr>
                    <tr><td>Current Liabilities</td><td>10.63</td><td>6.56</td></tr>
                    <tr><td>Retained Earnings</td><td>33.62</td><td>13.55</td></tr>
                    <tr><td>Operating Cash Flow</td><td>28.09</td><td>5.64</td></tr>
                </table>
            </main>
            <footer><div class="disclaimer-footer">All rights reserved SEC EDGAR 2024. <a href="/privacy">Privacy</a></div></footer>
        </body>
        </html>
        """,

        "reuters.com/tech/semiconductor-supply-chain": """
        <!DOCTYPE html>
        <html>
        <head><title>Global Semiconductor Supply Chain Matrix: TSMC, ASML, and Mega-Cap AI Infrastructure</title></head>
        <body>
            <div class="popup-modal">Subscribe to Reuters Breaking News</div>
            <article>
                <h1>Special Report: The Critical Triad of Global AI Compute</h1>
                <p>TAIPEI / VELDMHOVEN — At the epicenter of the global AI boom sits an interdependent chain of technology monopolies. <strong>ASML Holding N.V.</strong> remains the sole manufacturer of EUV photolithography machines, supplying equipment to <strong>Taiwan Semiconductor Manufacturing Company (TSMC)</strong>.</p>
                <p>In turn, TSMC manufactures cutting-edge silicon for <strong>Nvidia Corporation</strong>, <strong>Apple Inc.</strong>, and <strong>Advanced Micro Devices (AMD)</strong>. Over 90% of global super-computing chips are packaged in TSMC's CoWoS packaging facilities.</p>
                <p>Tech giants <strong>Microsoft Corp</strong> and <strong>Amazon Web Services</strong> serve as the primary buyers, accounting for an estimated 38% of Nvidia's data center GPU shipments. Both Microsoft and Amazon are concurrently developing proprietary silicon (Maia 100 and Trainium2) to mitigate supplier dependency.</p>
                <div class="social-share"><button>Share on LinkedIn</button><button>Tweet</button></div>
            </article>
        </body>
        </html>
        """
    }

    async def crawl(self, req: CrawlRequest) -> CrawlResponse:
        start_time = time.perf_counter()
        url = urllib.parse.urlsplit(req.url)
        if url.scheme not in {"http", "https"} or not url.hostname:
            raise ValueError("Enter an HTTP or HTTPS document URL.")

        fixture_key = url.netloc.lower() + url.path.rstrip("/")
        html = self.MOCK_DOMAINS.get(fixture_key)
        final_url = req.url
        status_code = 200
        content_type = "text/html; charset=utf-8"
        source = "fixture"

        if html is None:
            headers = {
                "User-Agent": self.USER_AGENTS[req.user_agent_mode],
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                async with httpx.AsyncClient(timeout=req.timeout_seconds, follow_redirects=True) as client:
                    response = await client.get(req.url, headers=headers)
                    response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise CrawlFetchError(f"Source returned HTTP {error.response.status_code}.") from error
            except httpx.InvalidURL as error:
                raise ValueError("Enter a valid document URL.") from error
            except httpx.RequestError as error:
                raise CrawlFetchError("Could not reach the source URL.") from error

            html = response.text
            final_url = str(response.url)
            status_code = response.status_code
            content_type = response.headers.get("content-type", "text/html")
            source = "web"

        if not html.strip():
            raise CrawlFetchError("The source returned an empty document.")
        title = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return CrawlResponse(
            url=final_url,
            status_code=status_code,
            content_type=content_type,
            raw_html_length=len(html),
            title=title.group(1).strip() if title else final_url,
            raw_html=html,
            extracted_links=self._extract_links(html, final_url) if req.extract_links else [],
            fetch_latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            crawled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            source=source,
        )

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        raw_hrefs = re.findall(r'href=[\'"]([^\'">]+)[\'"]', html, re.IGNORECASE)
        resolved = []
        for h in raw_hrefs:
            if h.startswith("#"):
                continue
            try:
                abs_url = urllib.parse.urljoin(base_url, h)
                scheme = urllib.parse.urlsplit(abs_url).scheme
            except ValueError:
                continue
            if scheme in {"http", "https"} and abs_url not in resolved:
                resolved.append(abs_url)
        return resolved[:25]
