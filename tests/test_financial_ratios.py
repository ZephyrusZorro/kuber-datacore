"""
Tests for Quantitative Financial Ratios, Altman Z-Score & Beneish M-Score.
"""

import pytest
from backend.financial_ratios import FinancialRatioEngine
from backend.sample_market_data import FINANCIAL_RECORDS


@pytest.fixture
def ratios():
    return FinancialRatioEngine()


def test_altman_z_nvda_safe_zone(ratios):
    nvda_metrics = FINANCIAL_RECORDS["NVDA"]
    res = ratios.calculate_altman_z(nvda_metrics)
    assert res.ticker == "NVDA"
    assert res.z_score > 2.99
    assert res.zone == "SAFE_ZONE"
    assert res.distress_probability_pct < 10.0


def test_beneish_m_score(ratios):
    nvda_metrics = FINANCIAL_RECORDS["NVDA"]
    res = ratios.calculate_beneish_m(nvda_metrics)
    assert res.ticker == "NVDA"
    assert "DSRI_ReceivablesIndex" in res.components
    assert res.manipulation_risk in ["UNLIKELY", "POSSIBLE", "HIGH_RISK"]


def test_comprehensive_valuation_report(ratios):
    report = ratios.generate_valuation_report("NVDA")
    assert report.ticker == "NVDA"
    assert report.gross_margin_pct > 70.0
    assert report.health_grade in ["AAA", "AA", "A"]
    assert report.altman_z.zone == "SAFE_ZONE"
