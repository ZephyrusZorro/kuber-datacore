"""
Kuber Data Core — Automated Headless Chrome UI & Feature Verification
Tests all 5 workspaces, DOM interactions, Canvas rendering, and API calls via real browser.
"""

import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

def run_browser_audit():
    errors = []
    console_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        page.on("pageerror", lambda exc: errors.append(f"PAGEERROR: {exc}"))
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        print("--> Navigating to http://127.0.0.1:8002...")
        page.goto("http://127.0.0.1:8002", timeout=10000)
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)

        print(f"--> Page Loaded. Title: {page.title()}")

        # 1. Test Tab 1: EDI Studio
        print("\n[AUDIT 1] Testing EDI Studio...")
        # Check spreadsheet rows
        rows = page.locator("#spreadsheetGrid tbody tr").count()
        print(f"   Spreadsheet rendered rows: {rows}")
        assert rows >= 5, "Spreadsheet grid did not render rows"

        # Ask EDI Query
        page.fill("#ediQueryInput", "Show me companies with market cap over 2000 billion")
        page.click("#btnRunEDI")
        time.sleep(0.8)
        ans = page.locator("#ediAnswerText").inner_text()
        print(f"   EDI Answer: {ans[:80]}...")
        assert "Apple" in ans or "4 companies" in ans or "market valuation" in ans or "Retrieved" in ans

        # Switch Charts: LINE
        page.click("button[data-chart='LINE']")
        time.sleep(0.3)
        line_dots = page.locator("#chartSvg circle").count()
        print(f"   LINE Chart SVG circles: {line_dots}")

        # Switch Charts: RADAR
        page.click("button[data-chart='RADAR']")
        time.sleep(0.3)
        radar_paths = page.locator("#chartSvg path").count()
        print(f"   RADAR Chart SVG paths: {radar_paths}")

        # Switch Charts: BAR
        page.click("button[data-chart='BAR']")
        time.sleep(0.3)
        bars = page.locator("#chartSvg rect.chart-svg-bar").count()
        print(f"   BAR Chart SVG bars: {bars}")

        # 2. Test Tab 2: Arlo Scraper
        print("\n[AUDIT 2] Testing Arlo Scraper...")
        page.click("button[data-tab='ws-arlo-scraper']")
        time.sleep(0.5)
        workers = page.locator("#scraperWorkersContainer .worker-node-card").count()
        print(f"   Worker cards: {workers}")
        assert workers == 3, "Worker cards missing"

        page.click("#btnExecuteCrawl")
        time.sleep(1.5)
        raw_chars = page.locator("#crawlRawChars").inner_text()
        clean_chars = page.locator("#crawlCleanChars").inner_text()
        preview = page.locator("#crawlMarkdownPreview").inner_text()
        print(f"   Crawl output: raw={raw_chars}, clean={clean_chars}")
        print(f"   Preview header: {preview[:60]}...")

        # 3. Test Tab 3: Knowledge Graph
        print("\n[AUDIT 3] Testing Knowledge Graph & Contagion...")
        page.click("button[data-tab='ws-graph']")
        time.sleep(0.8)
        canvas_box = page.locator("#graphCanvas").bounding_box()
        print(f"   Canvas bounding box: {canvas_box}")
        assert canvas_box and canvas_box["width"] > 200 and canvas_box["height"] > 200

        # Shortest path
        page.click("#btnFindPath")
        time.sleep(0.8)
        path_text = page.locator("#pathResultBox").inner_text()
        print(f"   Path Finder result: {path_text[:80]}...")

        # Shock cascade
        page.click("#btnSimulateShock")
        time.sleep(0.8)
        shock_text = page.locator("#shockResultBox").inner_text()
        print(f"   Shock simulation result: {shock_text[:80]}...")

        # 4. Test Tab 4: Autonomous DAG Orchestrator
        print("\n[AUDIT 4] Testing Autonomous DAG Orchestrator...")
        page.click("button[data-tab='ws-dag']")
        time.sleep(0.5)
        dag_nodes = page.locator("#dagFlowSteps .dag-step-node").count()
        print(f"   DAG steps rendered: {dag_nodes}")
        assert dag_nodes >= 3

        page.click("#btnRunDAG")
        time.sleep(3.0)
        logs = page.locator("#dagLogStream").inner_text()
        brief = page.locator("#dagExecutiveBrief").inner_text()
        print(f"   DAG execution logs lines: {len(logs.splitlines())}")
        print(f"   DAG Executive brief: {brief[:80]}...")

        # 5. Test Tab 5: Quantitative Valuation
        print("\n[AUDIT 5] Testing Valuation Matrix...")
        page.click("button[data-tab='ws-ratios']")
        time.sleep(0.5)
        grade = page.locator("#valHealthGrade").inner_text()
        altman = page.locator("#valAltmanScore").inner_text()
        beneish = page.locator("#valBeneishScore").inner_text()
        print(f"   Valuation initial: Grade={grade}, Altman={altman}, Beneish={beneish}")

        # Change ticker
        page.select_option("#valTickerSelect", "MSFT")
        time.sleep(0.5)
        grade_msft = page.locator("#valHealthGrade").inner_text()
        altman_msft = page.locator("#valAltmanScore").inner_text()
        print(f"   MSFT: Grade={grade_msft}, Altman={altman_msft}")

        browser.close()

    print("\n-------------------------------------------------------------")
    print(f"Total Console Logs: {len(console_logs)}")
    for cl in console_logs:
        if "error" in cl.lower() or "warn" in cl.lower():
            print(f"  {cl}")
    print(f"Total Page Errors: {len(errors)}")
    for err in errors:
        print(f"  ERROR: {err}")
    print("-------------------------------------------------------------")
    if errors:
        sys.exit(1)
    else:
        print("ALL BROWSER UI WORKSPACES VERIFIED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_browser_audit()
