"""
Kuber Data Core (कुबेर) — Enterprise Financial Knowledge Graph Engine
NetworkX-powered directed graph analytics, PageRank authority scoring,
multi-hop supply chain shortest paths, and systemic shock contagion simulation.
"""

from typing import List, Dict, Any, Optional, Tuple, Set, Union
import networkx as nx
from backend.models import (
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
        self.graph = nx.DiGraph()
        self.node_metadata: Dict[str, Dict[str, Any]] = {}
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
        self.graph.add_node(node_id)
        self.node_metadata[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "ticker": ticker,
            "sector": sector,
            "market_cap_b": market_cap_b,
            "risk_score": risk_score
        }

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: Union[RelationType, str],
        weight: float = 1.0,
        description: Optional[str] = None
    ) -> None:
        rel_str = relation.value if hasattr(relation, "value") else str(relation)
        edge_id = f"{source_id}-{rel_str}-{target_id}"
        self.graph.add_edge(
            source_id,
            target_id,
            id=edge_id,
            relation=rel_str,
            weight=weight,
            description=description
        )

    def get_view(self) -> KnowledgeGraphView:
        """Computes graph centrality metrics and packages view for frontend rendering."""
        # Compute PageRank
        try:
            pagerank_scores = nx.pagerank(self.graph, weight="weight", alpha=0.85)
        except Exception:
            pagerank_scores = {n: 1.0 / max(1, len(self.graph.nodes)) for n in self.graph.nodes}

        nodes_list: List[GraphNode] = []
        for n_id in self.graph.nodes:
            meta = self.node_metadata.get(n_id, {})
            degree = self.graph.degree(n_id)
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
        for u, v, data in self.graph.edges(data=True):
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

        density = round(nx.density(self.graph), 4)

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
        if source_id not in self.graph or target_id not in self.graph:
            return ShortestPathResponse(
                found=False,
                strategic_summary=f"One or both entities ('{source_id}', '{target_id}') not found in graph."
            )

        try:
            path_node_ids = nx.shortest_path(self.graph, source=source_id, target=target_id)
            path_edges: List[GraphEdge] = []

            for i in range(len(path_node_ids) - 1):
                u = path_node_ids[i]
                v = path_node_ids[i + 1]
                edge_data = self.graph.get_edge_data(u, v, {})
                path_edges.append(GraphEdge(
                    id=edge_data.get("id", f"{u}->{v}"),
                    source=u,
                    target=v,
                    relation=edge_data.get("relation", RelationType.SUPPLIES_TO),
                    weight=edge_data.get("weight", 1.0),
                    description=edge_data.get("description")
                ))

            # Generate strategic summary
            step_names = [self.node_metadata.get(nid, {}).get("label", nid) for nid in path_node_ids]
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
                undirected_path = nx.shortest_path(self.graph.to_undirected(), source=source_id, target=target_id)
                step_names = [self.node_metadata.get(nid, {}).get("label", nid) for nid in undirected_path]
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
        if shock_source_id not in self.graph:
            return ContagionSimulationResponse(
                shock_source_id=shock_source_id,
                source_label=shock_source_id,
                shock_magnitude_pct=shock_magnitude_pct,
                affected_nodes=[],
                total_market_cap_at_risk_b=0.0,
                systemic_risk_level="LOW",
                narrative_assessment="Node not found in graph."
            )

        source_meta = self.node_metadata.get(shock_source_id, {})
        source_label = source_meta.get("label", shock_source_id)

        # BFS shock propagation
        affected_impacts: List[ContagionNodeImpact] = []
        visited: Dict[str, float] = {shock_source_id: shock_magnitude_pct}
        queue: List[Tuple[str, int, float]] = [(shock_source_id, 0, shock_magnitude_pct)]

        total_cap_at_risk = 0.0
        if source_meta.get("market_cap_b"):
            total_cap_at_risk += source_meta["market_cap_b"] * (shock_magnitude_pct / 100.0)

        while queue:
            curr_id, distance, curr_shock = queue.pop(0)
            if distance >= 3 or curr_shock < 2.0:
                continue

            for successor in self.graph.successors(curr_id):
                edge_data = self.graph.get_edge_data(curr_id, successor, {})
                rel = edge_data.get("relation")
                edge_weight = edge_data.get("weight", 0.8)

                # Supply chain shocks propagate primarily down SUPPLIES_TO edges
                transmission_factor = edge_weight if rel == RelationType.SUPPLIES_TO else (edge_weight * 0.4)
                downstream_shock = curr_shock * transmission_factor * propagation_damping

                if successor not in visited or downstream_shock > visited[successor]:
                    visited[successor] = downstream_shock
                    succ_meta = self.node_metadata.get(successor, {})
                    succ_label = succ_meta.get("label", successor)
                    cap = succ_meta.get("market_cap_b", 0.0) or 0.0

                    exposure_channel = f"Direct Tier-{distance + 1} Supplier Dependency on {source_label}"
                    impact = ContagionNodeImpact(
                        node_id=successor,
                        label=succ_label,
                        hop_distance=distance + 1,
                        shock_intensity_pct=round(downstream_shock, 2),
                        exposure_channel=exposure_channel
                    )
                    affected_impacts.append(impact)
                    total_cap_at_risk += cap * (downstream_shock / 100.0)

                    queue.append((successor, distance + 1, downstream_shock))

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
