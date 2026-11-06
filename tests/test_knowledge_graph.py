"""
Tests for Financial Knowledge Graph Engine and Contagion Simulation.
"""

import pytest
from backend.knowledge_graph import KnowledgeGraphEngine


@pytest.fixture
def kg():
    return KnowledgeGraphEngine()


def test_knowledge_graph_view(kg):
    view = kg.get_view()
    assert view.total_nodes >= 10
    assert view.total_edges >= 10
    assert len(view.top_central_nodes) > 0
    assert view.graph_density > 0.0


def test_shortest_path_multi_hop(kg):
    # Path from ASML to NVDA (ASML -> TSM -> NVDA)
    res = kg.find_shortest_path("company-asml", "company-nvda")
    assert res.found is True
    assert "company-tsm" in res.path_nodes
    assert res.path_distance == 2
    assert "TSMC" in res.strategic_summary or "Taiwan Semiconductor" in res.strategic_summary


def test_contagion_simulation_tsmc_shock(kg):
    # Shock on TSMC propagates downstream to Nvidia, Apple, AMD
    res = kg.simulate_contagion("company-tsm", shock_magnitude_pct=40.0)
    assert res.shock_source_id == "company-tsm"
    assert len(res.affected_nodes) >= 3
    affected_ids = [n.node_id for n in res.affected_nodes]
    assert "company-nvda" in affected_ids
    assert "company-aapl" in affected_ids
    assert res.total_market_cap_at_risk_b > 500.0
    assert res.systemic_risk_level in ["ELEVATED", "SYSTEMIC_CRITICAL"]
