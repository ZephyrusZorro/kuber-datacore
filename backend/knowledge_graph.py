"""
Kuber Data Core (कुबेर) — Enterprise Financial Knowledge Graph Engine
NetworkX-powered directed graph analytics, PageRank authority scoring,
multi-hop supply chain shortest paths, and systemic shock contagion simulation.
"""

from threading import RLock
from typing import List, Dict, Any, Optional, Union
import networkx as nx
from backend.models import (
    ExtractedRelation,
    GraphNode,
    GraphEdge,
    KnowledgeGraphView,
    ShortestPathResponse,
    ContagionSimulationResponse,
    ContagionNodeImpact,
    EntityType,
    RelationType
)
from backend.sample_market_data import (
    CANONICAL_COMPANIES,
    CANONICAL_EXECUTIVES,
    CANONICAL_RELATIONSHIPS
)


class KnowledgeGraphEngine:
    """
    High-performance financial knowledge graph engine supporting multi-hop
    relational queries, degree centrality, PageRank, and supply chain contagion.
    """

    def __init__(self):
        self._lock = RLock()
        self._view_json: Optional[str] = None
        self._graph = nx.DiGraph()
        self._node_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialize_canonical_graph()

    def _initialize_canonical_graph(self) -> None:
        """Seed the graph with canonical technology companies and ecosystem relationships."""
        # Add Companies
        for c in CANONICAL_COMPANIES.values():
            self.add_node(
                node_id=c.canonical_id,
                label=c.name,
                node_type=c.entity_type,
                ticker=c.ticker,
                sector=c.sector,
                market_cap_b=c.market_cap_billions
            )

        # Add Executives
        for e in CANONICAL_EXECUTIVES.values():
            self.add_node(
                node_id=e.canonical_id,
                label=e.name,
                node_type=e.entity_type
            )

        # Add Strategic Relationships
        for r in CANONICAL_RELATIONSHIPS:
            self.add_edge(
                source_id=r["source"],
                target_id=r["target"],
                relation=r["relation"],
                weight=r["weight"],
                description=r["desc"]
            )

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: EntityType,
        ticker: Optional[str] = None,
        sector: Optional[str] = None,
        market_cap_b: Optional[float] = None,
        risk_score: float = 0.0
    ) -> None:
        with self._lock:
            self._graph.add_node(node_id)
            self._node_metadata[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "ticker": ticker,
                "sector": sector,
                "market_cap_b": market_cap_b,
                "risk_score": risk_score
            }
            self._view_json = None

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: Union[RelationType, str],
        weight: float = 1.0,
        description: Optional[str] = None
    ) -> None:
        rel_str = relation.value if isinstance(relation, RelationType) else relation
        attributes = {
            "id": f"{source_id}-{rel_str}-{target_id}",
            "relation": rel_str,
            "weight": weight,
            "description": description,
        }
        with self._lock:
            if self._graph.get_edge_data(source_id, target_id) != attributes:
                self._graph.add_edge(source_id, target_id, **attributes)
                self._view_json = None

    def add_relations(self, relations: List[ExtractedRelation]) -> None:
        with self._lock:
            for relation in relations:
                self.add_edge(
                    relation.source_entity_id,
                    relation.target_entity_id,
                    relation.relation_type,
                    relation.weight,
                    relation.evidence_quote,
                )

    def get_view_json(self) -> str:
        with self._lock:
            if self._view_json is None:
                self._view_json = self._build_view().model_dump_json()
            return self._view_json

    def get_view(self) -> KnowledgeGraphView:
        return KnowledgeGraphView.model_validate_json(self.get_view_json())

    def _calculate_pagerank(self) -> Dict[str, float]:
        """Weighted power iteration for the local graph, including dangling nodes."""
        size = len(self._graph)
        if not size:
            return {}
        alpha = 0.85
        degrees = dict(self._graph.out_degree(weight="weight"))
        dangling = [node for node, degree in degrees.items() if degree == 0]
        incoming = {
            node: [(source, weight / degrees[source]) for source, _, weight in self._graph.in_edges(node, data="weight", default=1)
                   if degrees[source] != 0]
            for node in self._graph
        }
        ranks = dict.fromkeys(self._graph, 1 / size)
        for _ in range(100):
            base = (1 - alpha + alpha * sum(ranks[node] for node in dangling)) / size
            updated = {
                node: base + alpha * sum(ranks[source] * ratio for source, ratio in links)
                for node, links in incoming.items()
            }
            if sum(abs(updated[node] - ranks[node]) for node in ranks) < size * 1e-6:
                return updated
            ranks = updated
        return dict.fromkeys(self._graph, 1 / size)

    def _build_view(self) -> KnowledgeGraphView:
        pagerank_scores = self._calculate_pagerank()
        nodes_list: List[GraphNode] = []
        for n_id in self._graph.nodes:
            meta = self._node_metadata.get(n_id, {})
            degree = self._graph.degree(n_id)
            pr = round(pagerank_scores.get(n_id, 0.0) * 100.0, 3)

            nodes_list.append(GraphNode(
                id=n_id,
                label=meta.get("label", n_id),
                type=meta.get("type", EntityType.COMPANY),
                ticker=meta.get("ticker"),
                sector=meta.get("sector"),
                market_cap_b=meta.get("market_cap_b"),
                degree=degree,
                pagerank=pr,
                risk_score=meta.get("risk_score", 0.0)
            ))

        edges_list: List[GraphEdge] = []
        for u, v, data in self._graph.edges(data=True):
            edges_list.append(GraphEdge(
                id=data.get("id", f"{u}->{v}"),
                source=u,
                target=v,
                relation=data.get("relation", RelationType.SUPPLIES_TO),
                weight=data.get("weight", 1.0),
                description=data.get("description")
            ))

        # Top central nodes
        sorted_by_pr = sorted(nodes_list, key=lambda x: x.pagerank, reverse=True)
        top_central = [f"{n.label} ({n.ticker or n.id})" for n in sorted_by_pr[:5]]

        density = round(nx.density(self._graph), 4)

        return KnowledgeGraphView(
            nodes=nodes_list,
            edges=edges_list,
            total_nodes=len(nodes_list),
            total_edges=len(edges_list),
            graph_density=density,
            top_central_nodes=top_central
        )

    def find_shortest_path(self, source_id: str, target_id: str) -> ShortestPathResponse:
        """Finds multi-hop relational path connecting two nodes with strategic context."""
        with self._lock:
            if source_id not in self._graph or target_id not in self._graph:
                return ShortestPathResponse(
                    found=False,
                    strategic_summary=f"One or both entities ('{source_id}', '{target_id}') not found in graph."
                )

            try:
                path_node_ids = nx.shortest_path(self._graph, source=source_id, target=target_id)
                path_edges: List[GraphEdge] = []

                for i in range(len(path_node_ids) - 1):
                    u = path_node_ids[i]
                    v = path_node_ids[i + 1]
                    edge_data = self._graph.get_edge_data(u, v, {})
                    path_edges.append(GraphEdge(
                        id=edge_data.get("id", f"{u}->{v}"),
                        source=u,
                        target=v,
                        relation=edge_data.get("relation", RelationType.SUPPLIES_TO),
                        weight=edge_data.get("weight", 1.0),
                        description=edge_data.get("description")
                    ))

                # Generate strategic summary
                step_names = [self._node_metadata.get(nid, {}).get("label", nid) for nid in path_node_ids]
                summary = " → ".join(step_names) + f" ({len(path_edges)} hop{'s' if len(path_edges) > 1 else ''}). Critical supply chain pathway."

                return ShortestPathResponse(
                    found=True,
                    path_nodes=path_node_ids,
                    path_edges=path_edges,
                    path_distance=len(path_edges),
                    strategic_summary=summary
                )
            except nx.NetworkXNoPath:
                # Check undirected fallback
                try:
                    undirected_path = nx.shortest_path(self._graph.to_undirected(), source=source_id, target=target_id)
                    step_names = [self._node_metadata.get(nid, {}).get("label", nid) for nid in undirected_path]
                    return ShortestPathResponse(
                        found=True,
                        path_nodes=undirected_path,
                        path_edges=[],
                        path_distance=len(undirected_path) - 1,
                        strategic_summary="Indirect bidirectional relationship: " + " ↔ ".join(step_names)
                    )
                except Exception:
                    return ShortestPathResponse(
                        found=False,
                        strategic_summary=f"No connected pathway between '{source_id}' and '{target_id}'."
                    )

    def simulate_contagion(
        self,
        shock_source_id: str,
        shock_magnitude_pct: float = 35.0,
        propagation_damping: float = 0.75
    ) -> ContagionSimulationResponse:
        """
        Simulates systemic supply chain shock propagation down the directed graph.
        If an upstream node fails (e.g. TSMC or ASML), quantifies shock cascade
        on downstream buyers (Nvidia, Apple, Microsoft, Amazon).
        """
        with self._lock:
            if shock_source_id not in self._graph:
                return ContagionSimulationResponse(
                    shock_source_id=shock_source_id,
                    source_label=shock_source_id,
                    shock_magnitude_pct=shock_magnitude_pct,
                    affected_nodes=[],
                    total_market_cap_at_risk_b=0.0,
                    systemic_risk_level="LOW",
                    narrative_assessment="Node not found in graph."
                )

            source_meta = self._node_metadata.get(shock_source_id, {})
            source_label = source_meta.get("label", shock_source_id)

            # Keep the strongest route at each hop, then count each entity once.
            frontier = {shock_source_id: shock_magnitude_pct}
            strongest: Dict[str, tuple[float, int]] = {}
            for hop in range(1, 4):
                following: Dict[str, float] = {}
                for current, shock in frontier.items():
                    if shock < 2.0:
                        continue
                    for successor, edge in self._graph[current].items():
                        if successor == shock_source_id:
                            continue
                        relation_factor = 1.0 if edge["relation"] == RelationType.SUPPLIES_TO else 0.4
                        impact = shock * edge["weight"] * relation_factor * propagation_damping
                        if impact > following.get(successor, -1.0):
                            following[successor] = impact
                        if successor not in strongest or impact > strongest[successor][0]:
                            strongest[successor] = (impact, hop)
                frontier = following

            total_cap_at_risk = (source_meta.get("market_cap_b") or 0.0) * shock_magnitude_pct / 100
            affected_impacts = []
            for node_id, (impact, hop) in strongest.items():
                metadata = self._node_metadata.get(node_id, {})
                total_cap_at_risk += (metadata.get("market_cap_b") or 0.0) * impact / 100
                affected_impacts.append(ContagionNodeImpact(
                    node_id=node_id,
                    label=metadata.get("label", node_id),
                    hop_distance=hop,
                    shock_intensity_pct=round(impact, 2),
                    exposure_channel=f"Tier-{hop} dependency on {source_label}",
                ))

            # Risk tier determination
            if total_cap_at_risk > 1500.0 or shock_magnitude_pct >= 40.0:
                risk_level = "SYSTEMIC_CRITICAL"
            elif total_cap_at_risk > 600.0:
                risk_level = "ELEVATED"
            elif total_cap_at_risk > 150.0:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            narrative = (
                f"A {shock_magnitude_pct:.1f}% operational or geopolitical disruption to {source_label} "
                f"cascades across {len(affected_impacts)} downstream enterprise nodes, placing an estimated "
                f"${total_cap_at_risk:,.1f}B in aggregate market capitalization at direct operational risk. "
                f"Highest second-order vulnerability concentrates in high-volume CoWoS packaging and hyperscaler cloud deployments."
            )

            return ContagionSimulationResponse(
                shock_source_id=shock_source_id,
                source_label=source_label,
                shock_magnitude_pct=shock_magnitude_pct,
                affected_nodes=affected_impacts,
                total_market_cap_at_risk_b=round(total_cap_at_risk, 1),
                systemic_risk_level=risk_level,
                narrative_assessment=narrative
            )
