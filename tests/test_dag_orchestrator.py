"""
Tests for Autonomous DAG Pipeline Orchestrator.
"""

import pytest
from backend.dag_orchestrator import DAGOrchestrator
from backend.web_crawler import WebCrawlerEngine
from backend.dom_pruner import DOMPruningEngine
from backend.entity_linker import EntityLinkingEngine
from backend.knowledge_graph import KnowledgeGraphEngine
from backend.financial_ratios import FinancialRatioEngine
from backend.models import DAGNodeStatus


@pytest.fixture
def orchestrator():
    return DAGOrchestrator(
        crawler=WebCrawlerEngine(),
        pruner=DOMPruningEngine(),
        linker=EntityLinkingEngine(),
        kg=KnowledgeGraphEngine(),
        ratios=FinancialRatioEngine()
    )


def test_list_preset_pipelines(orchestrator):
    pipelines = orchestrator.list_pipelines()
    assert len(pipelines) >= 2
    ids = [p.pipeline_id for p in pipelines]
    assert "financial-cortex-e2e" in ids


@pytest.mark.anyio
async def test_execute_e2e_dag_pipeline(orchestrator):
    run = await orchestrator.execute_pipeline("financial-cortex-e2e")
    assert run.status == DAGNodeStatus.COMPLETED
    assert run.total_duration_ms > 0.0
    assert len(run.execution_logs) >= 5

    # Check node completion
    for node_id, state in run.nodes_state.items():
        assert state.status == DAGNodeStatus.COMPLETED
        assert state.duration_ms >= 0.0

    # Check executive brief artifact
    assert "executive_brief" in run.run_artifacts
    assert "EXECUTIVE INTELLIGENCE BRIEF" in run.run_artifacts["executive_brief"]

@pytest.mark.anyio
async def test_pipeline_processes_the_selected_source(orchestrator):
    run = await orchestrator.execute_pipeline(
        "financial-cortex-e2e",
        custom_params={"node-1-crawl": {"url": "https://reuters.com/tech/semiconductor-supply-chain"}},
    )
    assert run.status == DAGNodeStatus.COMPLETED
    assert "The Critical Triad of Global AI Compute" in run.run_artifacts["markdown_content"]

@pytest.mark.anyio
async def test_failed_fetch_leaves_a_terminal_pipeline_state(orchestrator):
    run = await orchestrator.execute_pipeline(
        "financial-cortex-e2e",
        custom_params={"node-1-crawl": {"url": "file:///private.txt"}},
    )
    assert run.status == DAGNodeStatus.FAILED
    assert run.nodes_state["node-1-crawl"].completed_at
    assert run.nodes_state["node-1-crawl"].status == DAGNodeStatus.FAILED
    assert all(state.status in {DAGNodeStatus.FAILED, DAGNodeStatus.SKIPPED}
               for state in run.nodes_state.values())
    assert "executive_brief" not in run.run_artifacts
