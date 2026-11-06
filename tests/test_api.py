"""
FastAPI HTTP Endpoint Integration Tests for Kuber Data Core.
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Kuber Data Core" in data["service"]


def test_api_crawler_and_prune(client):
    crawl_resp = client.post("/api/crawler/crawl", json={"url": "https://sec.gov/edgar/nvda-10k"})
    assert crawl_resp.status_code == 200
    assert "NVIDIA" in crawl_resp.json()["title"]

    prune_resp = client.post("/api/crawler/prune", json={
        "raw_html": "<html><body><h1>Title</h1><p>Content</p><script>bad();</script></body></html>",
        "strategy": "PRUNING_LXML"
    })
    assert prune_resp.status_code == 200
    assert "# Title" in prune_resp.json()["markdown_content"]


def test_api_entity_linking(client):
    resp = client.post("/api/entities/link", json={
        "document_text": "TSMC manufactures advanced chips for Nvidia and Apple.",
        "confidence_threshold": 0.70
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_mentions"] >= 2


def test_api_graph_endpoints(client):
    view_resp = client.get("/api/graph/view")
    assert view_resp.status_code == 200
    assert view_resp.json()["total_nodes"] >= 10

    path_resp = client.post("/api/graph/shortest-path", json={
        "source_id": "company-asml",
        "target_id": "company-nvda"
    })
    assert path_resp.status_code == 200
    assert path_resp.json()["found"] is True

    contagion_resp = client.post("/api/graph/simulate-contagion", json={
        "shock_source_id": "company-tsm",
        "shock_magnitude_pct": 35.0
    })
    assert contagion_resp.status_code == 200
    assert len(contagion_resp.json()["affected_nodes"]) >= 3


def test_api_financial_valuation(client):
    resp = client.get("/api/financials/ratios/NVDA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "NVDA"
    assert data["altman_z"]["zone"] == "SAFE_ZONE"

    tickers_resp = client.get("/api/financials/tickers")
    assert tickers_resp.status_code == 200
    assert len(tickers_resp.json()) >= 5


def test_api_dag_pipeline_execution(client):
    list_resp = client.get("/api/dag/pipelines")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    exec_resp = client.post("/api/dag/execute/financial-cortex-e2e", json={})
    assert exec_resp.status_code == 200
    run_data = exec_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert "node-1-crawl" in run_data["nodes_state"]


def test_api_edi_natural_query(client):
    resp = client.post("/api/edi/query", json={
        "natural_query": "Rank all companies by market cap"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "MARKET_CAP_ANALYSIS"
    assert len(data["rows"]) >= 1


def test_api_edi_spreadsheet_and_chart(client):
    # Test GET sheet
    sheet_resp = client.get("/api/edi/sheet")
    assert sheet_resp.status_code == 200
    sheet = sheet_resp.json()
    assert sheet["total_rows"] >= 5
    assert "ticker" in sheet["columns"]

    # Test UPDATE cell
    update_resp = client.post("/api/edi/sheet/update", json={
        "ticker": "NVDA",
        "column": "market_cap_b",
        "value": 3200.0
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "updated"

    # Test GET chart
    chart_resp = client.get("/api/edi/chart?chart_type=BAR")
    assert chart_resp.status_code == 200
    chart = chart_resp.json()
    assert chart["chart_type"] == "BAR"
    assert len(chart["series"]) >= 1

    # Test Scraper Workers
    workers_resp = client.get("/api/crawler/workers")
    assert workers_resp.status_code == 200
    assert len(workers_resp.json()) == 3

    # Test Scrape to Sheet
    scrape_resp = client.post("/api/crawler/scrape-to-sheet", json={
        "url": "https://sec.gov/edgar/nvda-10k"
    })
    assert scrape_resp.status_code == 200
    assert scrape_resp.json()["status"] == "success"
