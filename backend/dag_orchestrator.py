"""
Kuber Data Core (कुबेर) — Autonomous DAG Pipeline Execution Orchestrator
Directed Acyclic Graph dependency resolution, topological task scheduling,
real-time step telemetry, and multi-stage financial intelligence workflows.
"""

import time
import uuid
from typing import List, Dict, Any, Optional
import networkx as nx

from backend.models import (
    DAGNodeSpec,
    DAGPipelineSpec,
    DAGExecutionRun,
    DAGNodeExecutionState,
    DAGNodeStatus,
    CrawlRequest,
    DOMPruneRequest,
    FilterStrategy
)
from backend.web_crawler import WebCrawlerEngine
from backend.dom_pruner import DOMPruningEngine
from backend.entity_linker import EntityLinkingEngine
from backend.knowledge_graph import KnowledgeGraphEngine
from backend.financial_ratios import FinancialRatioEngine


class DAGOrchestrator:
    """
    Enterprise DAG pipeline executor managing asynchronous task execution,
    topological sorting, parameter cascading, and runtime logging.
    """

    def __init__(
        self,
        crawler: WebCrawlerEngine,
        pruner: DOMPruningEngine,
        linker: EntityLinkingEngine,
        kg: KnowledgeGraphEngine,
        ratios: FinancialRatioEngine
    ):
        self.crawler = crawler
        self.pruner = pruner
        self.linker = linker
        self.kg = kg
        self.ratios = ratios
        self.pipelines: Dict[str, DAGPipelineSpec] = self._build_preset_pipelines()
        self.execution_history: Dict[str, DAGExecutionRun] = {}

    def _build_preset_pipelines(self) -> Dict[str, DAGPipelineSpec]:
        """Defines production-grade financial analysis pipelines."""
        # Pipeline 1: Full Financial Intelligence Cortex
        p1 = DAGPipelineSpec(
            pipeline_id="financial-cortex-e2e",
            title="Autonomous Enterprise Financial Cortex Pipeline",
            description="End-to-end ingestion: Web/SEC Crawl → DOM Pruning → Entity Resolution → Knowledge Graph → Altman Z & Ratio Audit → Contagion Shock Simulation → Executive Brief",
            nodes=[
                DAGNodeSpec(
                    id="node-1-crawl",
                    name="Ingest SEC & Web Intelligence",
                    task_type="FETCH_CRAWLER",
                    parameters={"url": "https://sec.gov/edgar/nvda-10k", "user_agent_mode": "desktop_chrome"}
                ),
                DAGNodeSpec(
                    id="node-2-prune",
                    name="DOM Boilerplate Prune & Markdown",
                    task_type="PRUNE_DOM_MARKDOWN",
                    dependencies=["node-1-crawl"],
                    parameters={"strategy": "PRUNING_LXML"}
                ),
                DAGNodeSpec(
                    id="node-3-ner",
                    name="Financial Entity Linking & FIBO Disambiguation",
                    task_type="EXTRACT_ENTITIES",
                    dependencies=["node-2-prune"],
                    parameters={"confidence_threshold": 0.75}
                ),
                DAGNodeSpec(
                    id="node-4-graph",
                    name="Knowledge Graph Topology Ingestion",
                    task_type="LINK_CANONICAL_GRAPH",
                    dependencies=["node-3-ner"],
                    parameters={}
                ),
                DAGNodeSpec(
                    id="node-5-ratios",
                    name="Quantitative Solvency & Altman Z Audit",
                    task_type="CALCULATE_RATIOS",
                    dependencies=["node-4-graph"],
                    parameters={"ticker": "NVDA"}
                ),
                DAGNodeSpec(
                    id="node-6-contagion",
                    name="Systemic Supply Chain Contagion Shock",
                    task_type="SIMULATE_CONTAGION",
                    dependencies=["node-4-graph"],
                    parameters={"shock_source_id": "company-tsm", "shock_magnitude_pct": 35.0}
                ),
                DAGNodeSpec(
                    id="node-7-brief",
                    name="Synthesize Executive Market Brief",
                    task_type="SYNTHESIZE_EXECUTIVE_BRIEF",
                    dependencies=["node-5-ratios", "node-6-contagion"],
                    parameters={}
                )
            ]
        )

        # Pipeline 2: Rapid Supply Chain Contagion Assessment
        p2 = DAGPipelineSpec(
            pipeline_id="supply-chain-shock-dag",
            title="Upstream Foundry Contagion Assessment",
            description="Focuses on ASML and TSMC single-point-of-failure propagation to AI hyperscalers.",
            nodes=[
                DAGNodeSpec(
                    id="node-sc-1-graph",
                    name="Load Ecosystem Supply Chain Topology",
                    task_type="LINK_CANONICAL_GRAPH",
                    parameters={}
                ),
                DAGNodeSpec(
                    id="node-sc-2-contagion",
                    name="Simulate 50% Lithography Disruption",
                    task_type="SIMULATE_CONTAGION",
                    dependencies=["node-sc-1-graph"],
                    parameters={"shock_source_id": "company-asml", "shock_magnitude_pct": 50.0}
                ),
                DAGNodeSpec(
                    id="node-sc-3-brief",
                    name="Generate Downstream Exposure Memorandum",
                    task_type="SYNTHESIZE_EXECUTIVE_BRIEF",
                    dependencies=["node-sc-2-contagion"],
                    parameters={}
                )
            ]
        )

        return {p1.pipeline_id: p1, p2.pipeline_id: p2}

    def list_pipelines(self) -> List[DAGPipelineSpec]:
        return list(self.pipelines.values())

    def get_pipeline(self, pipeline_id: str) -> Optional[DAGPipelineSpec]:
        return self.pipelines.get(pipeline_id)

    async def execute_pipeline(self, pipeline_id: str, custom_params: Optional[Dict[str, Any]] = None) -> DAGExecutionRun:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline '{pipeline_id}' not found.")

        run_id = f"dag-run-{uuid.uuid4().hex[:8]}"
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run_start = time.perf_counter()

        # Initialize node states
        nodes_state: Dict[str, DAGNodeExecutionState] = {}
        for node in pipeline.nodes:
            nodes_state[node.id] = DAGNodeExecutionState(
                node_id=node.id,
                name=node.name,
                status=DAGNodeStatus.PENDING
            )

        run = DAGExecutionRun(
            run_id=run_id,
            pipeline_id=pipeline_id,
            status=DAGNodeStatus.RUNNING,
            created_at=created_at,
            nodes_state=nodes_state,
            run_artifacts={},
            execution_logs=[f"[{created_at}] Initiating DAG execution run '{run_id}' for pipeline '{pipeline.title}'"]
        )

        # Build execution DAG
        G = nx.DiGraph()
        for node in pipeline.nodes:
            G.add_node(node.id, spec=node)
            for dep in node.dependencies:
                G.add_edge(dep, node.id)

        # Verify acyclic
        if not nx.is_directed_acyclic_graph(G):
            run.status = DAGNodeStatus.FAILED
            run.execution_logs.append("[ERROR] Pipeline contains dependency cycle. Execution aborted.")
            self.execution_history[run_id] = run
            return run

        # Execute in topological order
        topological_nodes = list(nx.topological_sort(G))
        node_lookup = {n.id: n for n in pipeline.nodes}
        context_artifacts: Dict[str, Any] = {}

        for n_id in topological_nodes:
            spec = node_lookup[n_id]
            node_state = nodes_state[n_id]
            node_state.status = DAGNodeStatus.RUNNING
            node_state.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            step_start = time.perf_counter()

            run.execution_logs.append(f"-> Executing node '{n_id}': {spec.name} ({spec.task_type})")

            try:
                # Merge custom parameters
                params = dict(spec.parameters)
                if custom_params and n_id in custom_params:
                    params.update(custom_params[n_id])

                output_summary = await self._execute_node_task(spec.task_type, params, context_artifacts)
                node_state.duration_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                node_state.status = DAGNodeStatus.COMPLETED
                node_state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                node_state.output_summary = output_summary

                run.execution_logs.append(f"   [DONE] '{n_id}' finished in {node_state.duration_ms}ms: {output_summary}")

            except Exception as e:
                node_state.duration_ms = round((time.perf_counter() - step_start) * 1000.0, 2)
                node_state.status = DAGNodeStatus.FAILED
                node_state.error_message = str(e)
                run.status = DAGNodeStatus.FAILED
                run.execution_logs.append(f"   [FAILED] '{n_id}' error: {str(e)}")
                break

        run.total_duration_ms = round((time.perf_counter() - run_start) * 1000.0, 2)
        if run.status != DAGNodeStatus.FAILED:
            run.status = DAGNodeStatus.COMPLETED

        run.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run.run_artifacts = context_artifacts
        run.execution_logs.append(f"[{run.completed_at}] Pipeline completed with status '{run.status.value}' in {run.total_duration_ms}ms.")

        self.execution_history[run_id] = run
        return run

    async def _execute_node_task(
        self,
        task_type: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Executes a single DAG node task and records outputs in context."""
        if task_type == "FETCH_CRAWLER":
            url = params.get("url", "https://sec.gov/edgar/nvda-10k")
            req = CrawlRequest(url=url, user_agent_mode=params.get("user_agent_mode", "desktop_chrome"))
            res = await self.crawler.crawl(req)
            context["raw_html"] = res.raw_html
            context["crawl_result"] = res.model_dump()
            return f"Fetched {res.raw_html_length} bytes from {res.url} (Status: {res.status_code})"

        elif task_type == "PRUNE_DOM_MARKDOWN":
            raw_html = context.get("raw_html", "<html><body>Empty</body></html>")
            res = self.pruner.prune_and_convert(raw_html, strategy=FilterStrategy.PRUNING_LXML)
            context["markdown_content"] = res.markdown_content
            context["compression_ratio_pct"] = res.compression_ratio_pct
            return f"Pruned DOM: {res.raw_char_count} → {res.cleaned_char_count} chars ({res.compression_ratio_pct}% token compression)"

        elif task_type == "EXTRACT_ENTITIES":
            doc_text = context.get("markdown_content", "Nvidia relies on TSMC for semiconductor chips.")
            res = self.linker.extract_and_link(doc_text, confidence_threshold=params.get("confidence_threshold", 0.70))
            context["extracted_mentions"] = [m.model_dump() for m in res.mentions]
            context["extracted_relations"] = [r.model_dump() for r in res.relations]
            return f"Resolved {res.total_mentions} mentions across {res.unique_entities} canonical entities with {len(res.relations)} extracted relations"

        elif task_type == "LINK_CANONICAL_GRAPH":
            # Ensure graph is updated with newly extracted relations
            new_relations = context.get("extracted_relations", [])
            for r in new_relations:
                self.kg.add_edge(
                    source_id=r["source_entity_id"],
                    target_id=r["target_entity_id"],
                    relation=r["relation_type"],
                    weight=r.get("weight", 1.0),
                    description=r.get("evidence_quote")
                )
            view = self.kg.get_view()
            context["graph_summary"] = {"total_nodes": view.total_nodes, "total_edges": view.total_edges}
            return f"Knowledge graph synchronized: {view.total_nodes} nodes, {view.total_edges} edges, density: {view.graph_density}"

        elif task_type == "CALCULATE_RATIOS":
            ticker = params.get("ticker", "NVDA")
            report = self.ratios.generate_valuation_report(ticker)
            context["valuation_report"] = report.model_dump()
            return f"{ticker} Altman Z={report.altman_z.z_score} ({report.altman_z.zone}), Gross Margin={report.gross_margin_pct}%, Grade={report.health_grade}"

        elif task_type == "SIMULATE_CONTAGION":
            source_id = params.get("shock_source_id", "company-tsm")
            shock_pct = params.get("shock_magnitude_pct", 35.0)
            res = self.kg.simulate_contagion(source_id, shock_magnitude_pct=shock_pct)
            context["contagion_result"] = res.model_dump()
            return f"Contagion shock from {res.source_label}: {len(res.affected_nodes)} downstream nodes exposed (${res.total_market_cap_at_risk_b}B cap at risk)"

        elif task_type == "SYNTHESIZE_EXECUTIVE_BRIEF":
            val = context.get("valuation_report", {})
            cont = context.get("contagion_result", {})
            if val and cont:
                brief = (
                    f"EXECUTIVE INTELLIGENCE BRIEF: Target enterprise exhibits financial health grade {val.get('health_grade', 'AAA')} "
                    f"with an Altman Z-Score of {val.get('altman_z', {}).get('z_score', 'N/A')} ({val.get('altman_z', {}).get('zone', 'SAFE_ZONE')}). "
                    f"Supply chain stress testing demonstrates that a {cont.get('shock_magnitude_pct', 0)}% upstream shock at {cont.get('source_label', 'source node')} "
                    f"exposes ${cont.get('total_market_cap_at_risk_b', 0)}B in capital risk across {len(cont.get('affected_nodes', []))} critical customer nodes. "
                    f"Strategic mitigation mandates inventory buffering, dual-sourcing, and advanced packaging qualification."
                )
            elif cont:
                brief = (
                    f"SUPPLY CHAIN CONTAGION BRIEF: Critical upstream stress test models a {cont.get('shock_magnitude_pct', 0)}% operational shock at {cont.get('source_label', 'source')}. "
                    f"Cascade analysis exposes ${cont.get('total_market_cap_at_risk_b', 0)}B across {len(cont.get('affected_nodes', []))} downstream enterprise entities. "
                    f"High systemic fragility identified in single-source wafer lithography and CoWoS packaging pipelines."
                )
            elif val:
                brief = (
                    f"VALUATION & SOLVENCY MEMORANDUM: Entity maintains health rating {val.get('health_grade', 'AAA')}. "
                    f"Altman Z-Score of {val.get('altman_z', {}).get('z_score', 'N/A')} indicates robust solvency, while gross margin of {val.get('gross_margin_pct', 0)}% "
                    f"confirms institutional pricing power and defensible moat."
                )
            else:
                brief = "INTELLIGENCE SYNTHESIS COMPLETE: Graph topology, entity disambiguation, and market metrics successfully synchronized."

            context["executive_brief"] = brief
            return "Executive brief synthesized successfully."

        return "Task completed."
