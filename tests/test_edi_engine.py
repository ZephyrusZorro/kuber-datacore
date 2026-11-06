"""
Tests for EDI (Natural Language to SQL & Graph Traversal) Engine.
"""

import pytest
from backend.edi_query_engine import EDIQueryEngine
from backend.models import EDIQueryRequest


@pytest.fixture
def edi():
    return EDIQueryEngine()


def test_edi_market_cap_query(edi):
    req = EDIQueryRequest(natural_query="Show me companies with market cap over 2000 billion")
    res = edi.query(req)
    assert res.intent == "MARKET_CAP_ANALYSIS"
    assert "SELECT" in res.generated_sql
    assert len(res.rows) >= 2
    tickers = [r["ticker"] for r in res.rows]
    assert "NVDA" in tickers or "AAPL" in tickers or "MSFT" in tickers


def test_edi_operating_margin_query(edi):
    req = EDIQueryRequest(natural_query="Which tech company has the highest operating margin?")
    res = edi.query(req)
    assert res.intent == "PROFITABILITY_RANKING"
    assert len(res.rows) >= 1
    assert "operating_margin_pct" in res.column_headers


def test_edi_supply_chain_query(edi):
    req = EDIQueryRequest(natural_query="Who supplies chips to Nvidia?")
    res = edi.query(req)
    assert res.intent == "SUPPLY_CHAIN_INSPECTION"
    assert len(res.rows) >= 1
    assert res.generated_cypher is not None
    assert "TSM" in [r["source_name"] for r in res.rows] or "TSM" in [r["target_name"] for r in res.rows]


def test_edi_executive_lookup_query(edi):
    req = EDIQueryRequest(natural_query="Who is the CEO of Nvidia?")
    res = edi.query(req)
    assert res.intent == "EXECUTIVE_LOOKUP"
    assert len(res.rows) >= 1
    exec_names = [r["executive_name"] for r in res.rows]
    assert "Jensen Huang" in exec_names
