"""
Kuber Data Core (कुबेर) — Pydantic Schemas & Data Models
Enterprise Web Scraping, Financial Ontologies, Knowledge Graph & DAG Pipelines.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# --- Enums ---
class EntityType(str, Enum):
    COMPANY = "COMPANY"
    EXECUTIVE = "EXECUTIVE"
    SECTOR = "SECTOR"
    FILING = "FILING"
    PRODUCT = "PRODUCT"
    RISK_FACTOR = "RISK_FACTOR"
    MACRO_INDEX = "MACRO_INDEX"


class RelationType(str, Enum):
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLIES_TO = "SUPPLIES_TO"
    OFFICER_OF = "OFFICER_OF"
    EXPOSED_TO_RISK = "EXPOSED_TO_RISK"
    FILED_DOCUMENT = "FILED_DOCUMENT"
    PRODUCES = "PRODUCES"
    ACQUIRED = "ACQUIRED"
    PARTNERED_WITH = "PARTNERED_WITH"


class FilterStrategy(str, Enum):
    PRUNING_LXML = "PRUNING_LXML"
    BM25_RELEVANCE = "BM25_RELEVANCE"
    TOKEN_WINDOW_CHUNK = "TOKEN_WINDOW_CHUNK"


class DAGNodeStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class MarketRegime(str, Enum):
    BULL_MOMENTUM = "BULL_MOMENTUM"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    BEAR_CONTRACTION = "BEAR_CONTRACTION"
    NEUTRAL_CONSOLIDATION = "NEUTRAL_CONSOLIDATION"


# --- Web Crawler & DOM Pruner Models ---
class CrawlRequest(BaseModel):
    url: str
    max_depth: int = Field(default=1, ge=1, le=3)
    user_agent_mode: Literal["desktop_chrome", "data_bot", "financial_crawler"] = "desktop_chrome"
    extract_links: bool = True
    timeout_seconds: float = 10.0


class CrawlResponse(BaseModel):
    url: str
    status_code: int
    content_type: str
    raw_html_length: int
    title: str
    extracted_links: List[str] = Field(default_factory=list)
    fetch_latency_ms: float
    crawled_at: str


class DOMPruneRequest(BaseModel):
    raw_html: str
    strategy: FilterStrategy = FilterStrategy.PRUNING_LXML
    query_context: Optional[str] = None
    chunk_size_words: int = 400
    chunk_overlap_words: int = 50


class TextChunk(BaseModel):
    chunk_index: int
    heading_context: str
    word_count: int
    char_count: int
    content: str


class DOMPruneResponse(BaseModel):
    strategy: FilterStrategy
    raw_char_count: int
    cleaned_char_count: int
    compression_ratio_pct: float
    markdown_content: str
    chunks: List[TextChunk] = Field(default_factory=list)
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Entity Linking & Disambiguation Models ---
class CanonicalEntity(BaseModel):
    canonical_id: str
    entity_type: EntityType
    name: str
    ticker: Optional[str] = None
    cik: Optional[str] = None
    sector: Optional[str] = None
    country: str = "US"
    market_cap_billions: Optional[float] = None
    aliases: List[str] = Field(default_factory=list)


class EntityMention(BaseModel):
    raw_text: str
    start_char: int
    end_char: int
    confidence: float
    matched_canonical: CanonicalEntity


class ExtractedRelation(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    confidence: float
    evidence_quote: str
    weight: float = 1.0


class EntityLinkingRequest(BaseModel):
    document_text: str
    confidence_threshold: float = 0.70


class EntityLinkingResponse(BaseModel):
    total_mentions: int
    unique_entities: int
    mentions: List[EntityMention] = Field(default_factory=list)
    relations: List[ExtractedRelation] = Field(default_factory=list)


# --- Financial Knowledge Graph Models ---
class GraphNode(BaseModel):
    id: str
    label: str
    type: EntityType
    ticker: Optional[str] = None
    sector: Optional[str] = None
    market_cap_b: Optional[float] = None
    degree: int = 0
    pagerank: float = 0.0
    risk_score: float = 0.0  # 0.0 (Safe) to 1.0 (Critical)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    description: Optional[str] = None


class KnowledgeGraphView(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    graph_density: float = 0.0
    top_central_nodes: List[str] = Field(default_factory=list)


class ShortestPathRequest(BaseModel):
    source_id: str
    target_id: str


class ShortestPathResponse(BaseModel):
    found: bool
    path_nodes: List[str] = Field(default_factory=list)
    path_edges: List[GraphEdge] = Field(default_factory=list)
    path_distance: int = 0
    strategic_summary: str


class ContagionSimulationRequest(BaseModel):
    shock_source_id: str
    shock_magnitude_pct: float = Field(default=35.0, ge=1.0, le=100.0)
    propagation_damping: float = Field(default=0.75, ge=0.1, le=1.0)


class ContagionNodeImpact(BaseModel):
    node_id: str
    label: str
    hop_distance: int
    shock_intensity_pct: float
    exposure_channel: str


class ContagionSimulationResponse(BaseModel):
    shock_source_id: str
    source_label: str
    shock_magnitude_pct: float
    affected_nodes: List[ContagionNodeImpact] = Field(default_factory=list)
    total_market_cap_at_risk_b: float
    systemic_risk_level: Literal["LOW", "MODERATE", "ELEVATED", "SYSTEMIC_CRITICAL"]
    narrative_assessment: str


# --- Financial Statement & Ratio Analysis Models ---
class FinancialMetrics(BaseModel):
    ticker: str
    company_name: str
    fiscal_year: int
    revenue_billions: float
    gross_profit_billions: float
    operating_income_ebit_billions: float
    net_income_billions: float
    total_assets_billions: float
    total_liabilities_billions: float
    current_assets_billions: float
    current_liabilities_billions: float
    retained_earnings_billions: float
    market_cap_billions: float
    operating_cash_flow_billions: float


class AltmanZScoreResult(BaseModel):
    ticker: str
    z_score: float
    zone: Literal["SAFE_ZONE", "GREY_ZONE", "DISTRESS_ZONE"]
    distress_probability_pct: float
    components: Dict[str, float]
    clinical_interpretation: str


class BeneishMScoreResult(BaseModel):
    ticker: str
    m_score: float
    manipulation_risk: Literal["UNLIKELY", "POSSIBLE", "HIGH_RISK"]
    components: Dict[str, float]
    warning_signals: List[str] = Field(default_factory=list)


class ValuationReport(BaseModel):
    ticker: str
    company_name: str
    gross_margin_pct: float
    operating_margin_pct: float
    net_profit_margin_pct: float
    return_on_assets_pct: float
    return_on_equity_pct: float
    current_ratio: float
    debt_to_equity: float
    price_to_earnings: float
    altman_z: AltmanZScoreResult
    beneish_m: BeneishMScoreResult
    health_grade: Literal["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]


# --- DAG Orchestrator Models ---
class DAGNodeSpec(BaseModel):
    id: str
    name: str
    task_type: Literal[
        "FETCH_CRAWLER",
        "PRUNE_DOM_MARKDOWN",
        "EXTRACT_ENTITIES",
        "LINK_CANONICAL_GRAPH",
        "CALCULATE_RATIOS",
        "SIMULATE_CONTAGION",
        "SYNTHESIZE_EXECUTIVE_BRIEF"
    ]
    dependencies: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DAGNodeExecutionState(BaseModel):
    node_id: str
    name: str
    status: DAGNodeStatus = DAGNodeStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    output_summary: Optional[str] = None
    error_message: Optional[str] = None


class DAGPipelineSpec(BaseModel):
    pipeline_id: str
    title: str
    description: str
    nodes: List[DAGNodeSpec] = Field(default_factory=list)


class DAGExecutionRun(BaseModel):
    run_id: str
    pipeline_id: str
    status: DAGNodeStatus
    created_at: str
    completed_at: Optional[str] = None
    total_duration_ms: float = 0.0
    nodes_state: Dict[str, DAGNodeExecutionState] = Field(default_factory=dict)
    run_artifacts: Dict[str, Any] = Field(default_factory=dict)
    execution_logs: List[str] = Field(default_factory=list)


# --- Natural Language EDI Query Engine Models ---
class EDIQueryRequest(BaseModel):
    natural_query: str
    top_k: int = 15


class EDIQueryResponse(BaseModel):
    natural_query: str
    intent: str
    generated_sql: Optional[str] = None
    generated_cypher: Optional[str] = None
    column_headers: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    natural_language_answer: str
    execution_time_ms: float
    grounded_record_count: int


# --- Real-Time Market Ticker Model ---
class MarketTicker(BaseModel):
    ticker: str
    name: str
    price: float
    change_dollar: float
    change_pct: float
    volume_m: float
    sector: str
    updated_at: str
