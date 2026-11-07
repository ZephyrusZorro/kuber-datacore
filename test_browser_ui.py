"""Run all five workspaces against a running Kuber instance with Playwright."""

import argparse
import csv
import re

from playwright.sync_api import expect, sync_playwright


WORKSPACES = {
    "ws-edi-studio": "The research desk.",
    "ws-arlo-scraper": "Source lab.",
    "ws-graph": "Network atlas.",
    "ws-dag": "Pipeline studio.",
    "ws-ratios": "Valuation desk.",
}


def navigate(page, workspace):
    button = page.locator(f'[data-tab="{workspace}"]')
    button.click()
    expect(button).to_have_attribute("aria-current", "page")
    expect(page.get_by_role("heading", name=WORKSPACES[workspace], exact=True)).to_be_visible()


def check_research(page):
    worksheet = page.locator("#spreadsheetGrid")
    expect(worksheet.locator("tbody tr")).to_have_count(10)
    expect(page.locator("#chartSvg .chart-svg-bar")).to_have_count(6)
    page.locator("#ediQueryInput").fill("Market cap over $2T")
    page.locator("#btnRunEDI").click()
    expect(page.locator("#ediLatencyBadge")).to_contain_text("records")
    page.locator("#queryDetails summary").click()
    result = page.locator("#queryRecords tbody tr")
    tickers = result.locator("td:first-child").all_text_contents()
    caps = result.locator("td:nth-child(4)").all_text_contents()
    assert 0 < len(caps) < 10
    assert all(float(value.replace(",", "")) > 2000 for value in caps)
    chart_labels = page.locator("#chartSvg circle title").all_text_contents()
    assert [label.split(" · ")[0] for label in chart_labels] == tickers

    page.locator("#ediQueryInput").fill("Market cap over $900T")
    page.locator("#btnRunEDI").click()
    expect(page.locator("#ediLatencyBadge")).to_contain_text("0 records")
    expect(page.locator("#chartTitle")).not_to_contain_text("Query results")

    company = worksheet.locator('[data-ticker="NVDA"][data-column="company_name"]')
    original = company.get_attribute("data-value")
    literal = '=Example, "<img src=x>"'
    company.dblclick()
    formula = page.locator("#formulaInput")
    expect(formula).to_be_focused()
    formula.fill(literal)
    formula.press("Enter")
    try:
        expect(company).to_have_text(literal)
        expect(worksheet.locator("img")).to_have_count(0)
        with page.expect_download() as saved:
            page.locator("#btnExportCSV").click()
        with saved.value.path().open(encoding="utf-8", newline="") as exported:
            rows = {row["ticker"]: row for row in csv.DictReader(exported)}
        assert rows["NVDA"]["company_name"] == "'" + literal
    finally:
        expect(formula).to_be_enabled()
        formula.fill(original)
        formula.press("Enter")
        expect(company).to_have_text(original)
        expect(formula).to_be_enabled()

    cap = worksheet.locator('[data-ticker="NVDA"][data-column="market_cap_b"]')
    original_cap = cap.get_attribute("data-value")
    cap.click()
    formula.fill("1")
    formula.press("Enter")
    try:
        expect(worksheet.locator("tbody tr").last.locator('[data-column="ticker"]')).to_have_text("NVDA")
        expect(cap).to_have_attribute("aria-selected", "true")
    finally:
        expect(formula).to_be_enabled()
        formula.fill(original_cap)
        formula.press("Enter")
        expect(cap).to_have_attribute("data-value", original_cap)
        expect(formula).to_be_enabled()

    for chart, mark in [("LINE", "polyline"), ("RADAR", "polygon"), ("BAR", "rect.chart-svg-bar")]:
        pill = page.locator(f'[data-chart="{chart}"]')
        pill.click()
        expect(pill).to_have_attribute("aria-pressed", "true")
        expect(page.locator(f"#chartSvg {mark}").first).to_be_visible()


def check_source(page):
    navigate(page, "ws-arlo-scraper")
    expect(page.locator(".worker-node-card")).to_have_count(3)
    page.locator("#btnExecuteCrawl").click()
    expect(page.locator("#crawlSourceStatus")).to_have_text("Bundled sample document")
    expect(page.locator("#crawlMarkdownPreview")).to_contain_text("NVIDIA")
    page.locator("#crawlPresetSelect").select_option(index=1)
    page.locator("#btnScrapeToSheet").click()
    expect(page.locator("#crawlMarkdownPreview")).to_contain_text("The Critical Triad")
    expect(page.locator("#crawlEntities .small-badge").first).to_be_visible()
    page.locator("#pruneStrategySelect").select_option("TOKEN_WINDOW_CHUNK")
    page.locator("#btnExecuteCrawl").click()
    page.locator("#crawlChunkDetails summary").click()
    expect(page.locator("#crawlChunks article").first).to_contain_text("Chunk 1")
    page.locator("#pruneStrategySelect").select_option("BM25_RELEVANCE")
    page.locator("#crawlContextInput").fill("photolithography")
    page.locator("#btnExecuteCrawl").click()
    expect(page.locator("#crawlMarkdownPreview")).to_contain_text("photolithography")
    expect(page.locator("#crawlMarkdownPreview")).not_to_contain_text("The Critical Triad")
    page.locator("#crawlPresetSelect").select_option("custom")
    page.locator("#crawlUrlInput").fill("ftp://example.invalid/report")
    page.locator("#btnExecuteCrawl").click()
    expect(page.locator("#crawlSourceStatus")).to_have_text("Document could not be read.")
    expect(page.locator("#crawlMarkdownPreview")).to_contain_text("HTTP or HTTPS")


def check_graph(page):
    navigate(page, "ws-graph")
    canvas = page.locator("#graphCanvas")
    expect(canvas).to_be_visible()
    assert canvas.evaluate("(canvas) => canvas.width >= canvas.clientWidth && canvas.clientWidth > 250")
    assert canvas.evaluate("""canvas => {
        const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
        return pixels.some((value, index) => index % 4 === 3 && value > 0);
    }""")
    page.locator("#graphInspectSelect").select_option("company-nvda")
    expect(page.locator("#graphNodeDetail")).to_contain_text("Nvidia", ignore_case=True)
    page.locator("#pathSourceSelect").select_option("company-asml")
    page.locator("#pathTargetSelect").select_option("company-nvda")
    page.locator("#btnFindPath").click()
    expect(page.locator("#pathResultBox")).to_contain_text("Nvidia", ignore_case=True)
    page.locator("#shockSourceSelect").select_option("company-tsm")
    page.locator("#btnSimulateShock").click()
    expect(page.locator("#shockResultBox")).to_contain_text("modeled exposure")
    page.locator("#btnResetZoom").click()
    fitted = page.evaluate("visualizer.scale")
    page.get_by_role("button", name="Zoom in").click()
    assert page.evaluate("visualizer.scale") > fitted
    page.get_by_role("button", name="Zoom out").click()
    assert abs(page.evaluate("visualizer.scale") - fitted) < 0.001

    page.emulate_media(reduced_motion="reduce")
    counts = page.evaluate("""async () => {
        const canvas = document.getElementById("graphCanvas");
        const context = canvas.getContext("2d");
        const clear = context.clearRect;
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        let paints = 0;
        context.clearRect = function (...args) {
            paints++;
            return clear.apply(this, args);
        };
        await new Promise(resolve => setTimeout(resolve, 200));
        context.clearRect = clear;
        return paints;
    }""")
    assert counts == 0, f"Idle graph repainted {counts} times in 200 ms"
    page.emulate_media(reduced_motion="no-preference")
    page.locator("#btnResetZoom").click()
    page.wait_for_function("visualizer.physicsTicks === 0 && visualizer.renderFrame === null")


def check_pipeline_and_valuation(page):
    navigate(page, "ws-dag")
    for pipeline_id, brief in [
        ("financial-cortex-e2e", "EXECUTIVE INTELLIGENCE BRIEF"),
        ("supply-chain-shock-dag", "SUPPLY CHAIN CONTAGION BRIEF"),
    ]:
        page.locator("#dagPipelineSelect").select_option(pipeline_id)
        page.locator("#btnRunDAG").click()
        expect(page.locator("#dagRunStatus")).to_contain_text("COMPLETED")
        expect(page.locator(".dag-step-node.status-COMPLETED").first).to_be_visible()
        expect(page.locator("#dagExecutiveBrief")).to_contain_text(brief)
        expect(page.locator("#dagLogStream")).to_contain_text("[DONE]")

    navigate(page, "ws-ratios")
    expect(page.locator("#valAltmanScore")).to_have_text(re.compile(r"-?\d+\.\d{2}"))
    before = page.locator("#valAltmanScore").inner_text()
    page.locator("#valTickerSelect").select_option("MSFT")
    expect(page.locator("#valAltmanScore")).to_have_text(re.compile(r"-?\d+\.\d{2}"))
    assert page.locator("#valAltmanScore").inner_text() != before
    expect(page.locator("#valBeneishScore")).to_have_text(re.compile(r"-?\d+\.\d{2}"))


def run_browser_audit(base_url, channel=None):
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel)
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base_url)
        check_research(page)
        check_source(page)
        check_graph(page)
        check_pipeline_and_valuation(page)

        for width in (320, 390, 768, 1024, 1440):
            page.set_viewport_size({"width": width, "height": 844})
            for workspace in WORKSPACES:
                navigate(page, workspace)
                assert page.evaluate("document.documentElement.scrollWidth === innerWidth"), (width, workspace)
        page.emulate_media(reduced_motion="reduce")
        assert page.locator("#ws-ratios").evaluate("(node) => getComputedStyle(node).animationName") == "none"
        page.reload()
        expect(page.locator('[data-tab="ws-ratios"]')).to_have_attribute("aria-current", "page")
        assert page.evaluate("scrollY") == 0
        page.locator(".skip-link").focus()
        page.keyboard.press("Enter")
        expect(page.locator("#main")).to_be_focused()
        assert page.evaluate("location.hash") == "#ws-ratios"
        browser.close()

    assert not errors, errors
    print("Verified five Kuber workspaces and five viewport widths with no browser exceptions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8002")
    parser.add_argument("--channel", help="Installed browser channel, such as msedge or chrome")
    args = parser.parse_args()
    run_browser_audit(args.url, args.channel)
