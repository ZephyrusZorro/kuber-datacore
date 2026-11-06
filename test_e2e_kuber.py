"""
Kuber Data Core (कुबेर) — End-to-End Live Workflow Verification Script
Tests all 11 live subsystems against the running server on port 8002.
"""

import urllib.request
import json
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def post(url, payload):
    req = urllib.request.Request(
        "http://127.0.0.1:8002" + url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get(url):
    req = urllib.request.Request("http://127.0.0.1:8002" + url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


print("========================================================================")
print("  KUBER DATA CORE (कुबेर) — LIVE END-TO-END WORKFLOW VERIFICATION       ")
print("========================================================================")

# 1. Health
print("\n[TEST 1] Service Health & Engine Verification...")
health = get("/api/health")
print(f"   -> Status: {health['status']} | Service: {health['service']}")
assert health["status"] == "healthy"

# 2. Web Crawler
print("\n[TEST 2] Resilient Web Crawler (SEC EDGAR Ingestion)...")
crawl_res = post("/api/crawler/crawl", {
    "url": "https://sec.gov/edgar/nvda-10k",
    "user_agent_mode": "desktop_chrome"
})
print(f"   -> Title: {crawl_res['title']}")
print(f"   -> Status: {crawl_res['status_code']} | Raw HTML: {crawl_res['raw_html_length']} bytes | Latency: {crawl_res['fetch_latency_ms']}ms")
assert crawl_res["status_code"] == 200

# 3. DOM Pruning & Markdown
print("\n[TEST 3] Crawl4AI DOM Boilerplate Pruning & Token Compression...")
prune_res = post("/api/crawler/prune", {
    "raw_html": "<html><body><script>tracker();</script><div class='ad-banner'>Ad</div><main><h1>NVIDIA Form 10-K</h1><p>Revenue grew to $60.9B.</p></main></body></html>",
    "strategy": "PRUNING_LXML"
})
print(f"   -> Raw Chars: {prune_res['raw_char_count']} → Cleaned: {prune_res['cleaned_char_count']}")
print(f"   -> Token Compression: {prune_res['compression_ratio_pct']}%")
assert prune_res["compression_ratio_pct"] > 0.0

# 4. Entity Linking & NER
print("\n[TEST 4] Financial Entity Linking & Syntactic Relation Mining...")
ner_res = post("/api/entities/link", {
    "document_text": "ASML Holding N.V. supplies equipment to Taiwan Semiconductor Manufacturing Company for wafer fabrication. Jensen Huang is the CEO of NVIDIA Corporation.",
    "confidence_threshold": 0.70
})
print(f"   -> Mentions Resolved: {ner_res['total_mentions']} | Unique Entities: {ner_res['unique_entities']}")
print(f"   -> Relations Extracted: {len(ner_res['relations'])}")
for r in ner_res["relations"]:
    print(f"      - {r['source_entity_id']} --[{r['relation_type']}]--> {r['target_entity_id']} (Conf: {r['confidence']})")
assert ner_res["total_mentions"] >= 3

# 5. Knowledge Graph Topology
print("\n[TEST 5] Knowledge Graph Topology & PageRank Authority...")
kg_view = get("/api/graph/view")
print(f"   -> Total Nodes: {kg_view['total_nodes']} | Total Edges: {kg_view['total_edges']} | Density: {kg_view['graph_density']}")
print(f"   -> Top Central Authorities: {', '.join(kg_view['top_central_nodes'][:3])}")
assert kg_view["total_nodes"] >= 10

# 6. Multi-Hop Shortest Path
print("\n[TEST 6] Multi-Hop Supply Chain Shortest Path...")
path_res = post("/api/graph/shortest-path", {
    "source_id": "company-asml",
    "target_id": "company-nvda"
})
print(f"   -> Path Found: {path_res['found']} | Distance: {path_res['path_distance']} hops")
print(f"   -> Strategic Trace: {path_res['strategic_summary']}")
assert path_res["found"] is True

# 7. Contagion Shock Simulation
print("\n[TEST 7] Systemic Supply Chain Shock Simulation (TSMC Disruption)...")
shock_res = post("/api/graph/simulate-contagion", {
    "shock_source_id": "company-tsm",
    "shock_magnitude_pct": 35.0
})
print(f"   -> Source: {shock_res['source_label']} (-{shock_res['shock_magnitude_pct']}%)")
print(f"   -> Systemic Risk: {shock_res['systemic_risk_level']} | Capital at Risk: ${shock_res['total_market_cap_at_risk_b']}B")
print(f"   -> Downstream Exposed Nodes: {len(shock_res['affected_nodes'])}")
assert len(shock_res["affected_nodes"]) >= 3

# 8. Quantitative Solvency & Valuation
print("\n[TEST 8] Institutional Valuation & Altman Z Solvency...")
val_res = get("/api/financials/ratios/NVDA")
print(f"   -> Ticker: {val_res['ticker']} | Health Grade: {val_res['health_grade']}")
print(f"   -> Altman Z-Score: {val_res['altman_z']['z_score']} ({val_res['altman_z']['zone']})")
print(f"   -> Beneish M-Score: {val_res['beneish_m']['m_score']} ({val_res['beneish_m']['manipulation_risk']})")
print(f"   -> Gross Margin: {val_res['gross_margin_pct']}% | Operating Margin: {val_res['operating_margin_pct']}%")
assert val_res["altman_z"]["zone"] == "SAFE_ZONE"

# 9. Market Tickers
print("\n[TEST 9] Real-Time Market Ticker Tape Stream...")
tickers = get("/api/financials/tickers")
print(f"   -> Tickers in Stream: {len(tickers)}")
for t in tickers[:3]:
    print(f"      - {t['ticker']}: ${t['price']:.2f} ({t['change_pct']:+.2f}%) [{t['sector']}]")
assert len(tickers) >= 5

# 10. Autonomous DAG Execution
print("\n[TEST 10] Autonomous DAG Pipeline Execution (7-Step Cortex)...")
dag_res = post("/api/dag/execute/financial-cortex-e2e", {})
print(f"   -> Run ID: {dag_res['run_id']} | Status: {dag_res['status']} | Duration: {dag_res['total_duration_ms']}ms")
print(f"   -> Completed Steps: {len(dag_res['nodes_state'])} nodes")
print(f"   -> Executive Brief: {dag_res['run_artifacts'].get('executive_brief')[:90]}...")
assert dag_res["status"] == "COMPLETED"

# 11. EDI Natural Language SQL Engine
print("\n[TEST 11] EDI Natural Language to SQL ReAct Engine...")
edi_res = post("/api/edi/query", {
    "natural_query": "Show me companies with market cap over 2000 billion"
})
print(f"   -> Intent: {edi_res['intent']} | Exec Time: {edi_res['execution_time_ms']}ms")
print(f"   -> Synthesized SQL: {edi_res['generated_sql']}")
print(f"   -> Natural Answer: {edi_res['natural_language_answer']}")
print(f"   -> Rows Returned: {len(edi_res['rows'])}")
assert len(edi_res["rows"]) >= 2

# 12. EDI Spreadsheet Grid API
print("\n[TEST 12] EDI Interactive Spreadsheet Grid & Cell Updates...")
sheet_res = get("/api/edi/sheet")
print(f"   -> Columns: {len(sheet_res['columns'])} | Total Rows: {sheet_res['total_rows']}")
assert sheet_res["total_rows"] >= 5

cell_update = post("/api/edi/sheet/update", {
    "ticker": "NVDA",
    "column": "market_cap_b",
    "value": 3180.0
})
print(f"   -> Cell Updated: {cell_update['ticker']}.{cell_update['column']} = {cell_update['value']}")
assert cell_update["status"] == "updated"

# 13. Dynamic Recharts/SVG Chart Specifications
print("\n[TEST 13] Dynamic Recharts / SVG Chart Specifications...")
bar_chart = get("/api/edi/chart?chart_type=BAR")
print(f"   -> Bar Chart: '{bar_chart['title']}' | Series: {len(bar_chart['series'])}")
radar_chart = get("/api/edi/chart?chart_type=RADAR")
print(f"   -> Radar Chart: '{radar_chart['title']}' | Axes: {len(radar_chart['x_axis_labels'])}")
assert bar_chart["chart_type"] == "BAR"
assert radar_chart["chart_type"] == "RADAR"

# 14. Arlo Scraper Worker Pool Telemetry
print("\n[TEST 14] Arlo Scraper Distributed Worker Telemetry...")
workers = get("/api/crawler/workers")
print(f"   -> Active Worker Nodes: {len(workers)}")
for w in workers:
    print(f"      - {w['worker_id']}: {w['region']} ({w['latency_ms']}ms, {w['uptime_pct']}% uptime)")
assert len(workers) == 3

# 15. Arlo Scrape & Inject Directly Into Spreadsheet
print("\n[TEST 15] Arlo Scrape & Inject Directly into EDI Spreadsheet...")
scrape_to_sheet = post("/api/crawler/scrape-to-sheet", {
    "url": "https://sec.gov/edgar/nvda-10k"
})
print(f"   -> Status: {scrape_to_sheet['status']} | Ingested: {scrape_to_sheet['scraped_url']}")
print(f"   -> Parsed: {scrape_to_sheet['cleaned_bytes']} bytes ({scrape_to_sheet['compression_pct']}% token compression)")
print(f"   -> Sheet Rows Total: {scrape_to_sheet['sheet_total_rows']}")
assert scrape_to_sheet["status"] == "success"

print("\n========================================================================")
print("  SUCCESS: ALL 15 LIVE WORKFLOWS TESTED AND 100% OPERATIONAL!")
print("========================================================================")
