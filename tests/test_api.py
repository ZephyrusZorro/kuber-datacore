"""
FastAPI HTTP Endpoint Integration Tests for Kuber Data Core.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from starlette.testclient import TestClient
from backend import main
from backend.db import KuberDatabase


@pytest.fixture
def client(monkeypatch):
    with TemporaryDirectory(prefix="kuber-api-test-") as directory:
        monkeypatch.setattr(main, "db", KuberDatabase(Path(directory) / "test.db"))
        with TestClient(main.app) as test_client:
            yield test_client


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
    assert client.get("/api/dag/runs").json()[0]["run_id"] == run_data["run_id"]


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

def test_api_unknown_ticker_does_not_return_another_company(client):
    response = client.get("/api/financials/ratios/UNKNOWN")
    assert response.status_code == 404

def test_source_analysis_parses_once_and_keeps_raw_html_server_side(client, monkeypatch):
    source = "https://sec.gov/edgar/nvda-10k"
    prune = main.pruner_engine.prune_and_convert
    calls = []

    def record_prune(*args, **kwargs):
        calls.append(kwargs.get("strategy"))
        return prune(*args, **kwargs)

    monkeypatch.setattr(main.pruner_engine, "prune_and_convert", record_prune)
    response = client.post("/api/crawler/analyze", json={
        "url": source,
        "strategy": "TOKEN_WINDOW_CHUNK",
        "include_entities": True,
    })
    assert response.status_code == 200
    result = response.json()
    assert calls == ["TOKEN_WINDOW_CHUNK"]
    assert result["provenance"]["source"] == "fixture"
    assert result["provenance"]["url"] == source
    assert "raw_html" not in result["provenance"]
    assert "NVIDIA" in result["document"]["markdown_content"]
    assert result["document"]["chunks"]
    assert result["entity_names"]
    assert len(main.db.list_crawled_docs()) == 1

@pytest.mark.anyio
async def test_lifespan_crawlers_own_separate_pools():
    async with main.lifespan(main.app) as first:
        async with main.lifespan(main.app) as second:
            assert first["crawler"] is not second["crawler"]
            assert first["crawler"]._client is not second["crawler"]._client
        assert not first["crawler"]._client.is_closed
    assert first["crawler"]._client.is_closed
