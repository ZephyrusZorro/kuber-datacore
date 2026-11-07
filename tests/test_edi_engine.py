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


def test_market_cap_trillions_and_strict_threshold(edi):
    assert edi.update_cell("NVDA", "market_cap_b", 2500)
    report = edi.query(EDIQueryRequest(natural_query="Market cap over $2.5T"))
    assert report.rows
    assert all(row["market_cap_b"] > 2500 for row in report.rows)
    assert "NVDA" not in {row["ticker"] for row in report.rows}


@pytest.mark.parametrize("ticker,column,value", [
    ("NVDA", "ticker", "OTHER"),
    ("UNKNOWN", "revenue_b", "40"),
    ("NVDA", "revenue_b", "inf"),
    ("NVDA", "operating_margin_pct", "nan"),
])
def test_invalid_edits_do_not_change_spreadsheet(edi, ticker, column, value):
    before = edi.get_spreadsheet_data()
    assert not edi.update_cell(ticker, column, value)
    assert edi.get_spreadsheet_data() == before


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

def test_inclusive_market_cap_filter_includes_exact_boundary(edi):
    assert edi.update_cell("NVDA", "market_cap_b", 2500)
    result = edi.query(EDIQueryRequest(natural_query="Market cap >= $2.5T"))
    assert "NVDA" in {row["ticker"] for row in result.rows}
    assert all(row["market_cap_b"] >= 2500 for row in result.rows)

def test_market_cap_without_a_numeric_threshold_explains_the_input(edi):
    result = edi.query(EDIQueryRequest(natural_query="Market cap over a trillion"))
    assert not result.rows
    assert "numeric market-cap threshold" in result.natural_language_answer
