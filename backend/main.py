"""
Kuber Data Core (कुबेर) — Main FastAPI Application
Autonomous Distributed Web Intelligence, Financial Knowledge Graph & Market Cortex Service.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import (
    CrawlRequest,
    CrawlResponse,
    DOMPruneRequest,
    DOMPruneResponse,
    EntityLinkingRequest,
    EntityLinkingResponse,
    KnowledgeGraphView,
    ShortestPathRequest,
    ShortestPathResponse,
    ContagionSimulationRequest,
    ContagionSimulationResponse,
    ValuationReport,
    DAGPipelineSpec,
    DAGExecutionRun,
    EDIQueryRequest,
    EDIQueryResponse,
    ChartSpec,
    SpreadsheetData,
    SpreadsheetCellUpdate,
    MarketTicker
)
from backend.web_crawler import WebCrawlerEngine
from backend.dom_pruner import DOMPruningEngine
from backend.entity_linker import EntityLinkingEngine
from backend.knowledge_graph import KnowledgeGraphEngine
from backend.financial_ratios import FinancialRatioEngine
from backend.dag_orchestrator import DAGOrchestrator
from backend.edi_query_engine import EDIQueryEngine
from backend.sample_market_data import MARKET_TICKERS
from backend.db import KuberDatabase


app = FastAPI(
    title="Kuber Data Core (कुबेर)",
    description="Autonomous Web Intelligence, Financial Knowledge Graph & Market Cortex Pipeline",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Engines
db = KuberDatabase()
crawler_engine = WebCrawlerEngine()
pruner_engine = DOMPruningEngine()
linker_engine = EntityLinkingEngine()
kg_engine = KnowledgeGraphEngine()
ratio_engine = FinancialRatioEngine()
dag_orchestrator = DAGOrchestrator(
    crawler=crawler_engine,
    pruner=pruner_engine,
    linker=linker_engine,
    kg=kg_engine,
    ratios=ratio_engine
)
edi_engine = EDIQueryEngine()


# --- System Health ---
@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "service": "Kuber Data Core (कुबेर)",
        "version": "1.0.0",
        "engines": {
            "web_crawler": "active",
            "dom_pruner": "active",
            "entity_linker": "active",
            "knowledge_graph": "active",
            "ratio_engine": "active",
            "dag_orchestrator": "active",
            "edi_query_engine": "active"
        }
    }


# --- Crawler & DOM Pruner Endpoints ---
@app.post("/api/crawler/crawl", response_model=CrawlResponse)
async def crawl_web_page(req: CrawlRequest):
    res = await crawler_engine.crawl(req)
    # Automatically prune and save to db
    prune_res = pruner_engine.prune_and_convert(
        raw_html=crawler_engine.MOCK_DOMAINS.get(req.url, f"<html><body>{res.title}</body></html>")
    )
    db.save_crawled_doc(
        url=res.url,
        title=res.title,
        status_code=res.status_code,
        raw_length=res.raw_html_length,
        cleaned_length=prune_res.cleaned_char_count,
        compression_ratio=prune_res.compression_ratio_pct,
        markdown_preview=prune_res.markdown_content,
        crawled_at=res.crawled_at
    )
    return res


@app.post("/api/crawler/prune", response_model=DOMPruneResponse)
def prune_dom_content(req: DOMPruneRequest):
    return pruner_engine.prune_and_convert(
        raw_html=req.raw_html,
        strategy=req.strategy,
        query_context=req.query_context,
        chunk_size_words=req.chunk_size_words,
        chunk_overlap_words=req.chunk_overlap_words
    )


# --- Entity Linking & NER ---
@app.post("/api/entities/link", response_model=EntityLinkingResponse)
def link_financial_entities(req: EntityLinkingRequest):
    res = linker_engine.extract_and_link(
        text=req.document_text,
        confidence_threshold=req.confidence_threshold
    )
    # Add newly extracted relations into graph
    for r in res.relations:
        kg_engine.add_edge(
            source_id=r.source_entity_id,
            target_id=r.target_entity_id,
            relation=r.relation_type,
            weight=r.weight,
            description=r.evidence_quote
        )
    return res


# --- Knowledge Graph Endpoints ---
@app.get("/api/graph/view", response_model=KnowledgeGraphView)
def get_graph_view():
    return kg_engine.get_view()


@app.post("/api/graph/shortest-path", response_model=ShortestPathResponse)
def find_graph_path(req: ShortestPathRequest):
    return kg_engine.find_shortest_path(req.source_id, req.target_id)


@app.post("/api/graph/simulate-contagion", response_model=ContagionSimulationResponse)
def simulate_supply_chain_contagion(req: ContagionSimulationRequest):
    return kg_engine.simulate_contagion(
        shock_source_id=req.shock_source_id,
        shock_magnitude_pct=req.shock_magnitude_pct,
        propagation_damping=req.propagation_damping
    )


# --- Financial Ratios & Valuation ---
@app.get("/api/financials/ratios/{ticker}", response_model=ValuationReport)
def get_financial_valuation(ticker: str):
    return ratio_engine.generate_valuation_report(ticker.upper())


@app.get("/api/financials/tickers", response_model=List[MarketTicker])
def get_market_tickers():
    return MARKET_TICKERS


# --- Autonomous DAG Orchestrator ---
@app.get("/api/dag/pipelines", response_model=List[DAGPipelineSpec])
def list_dag_pipelines():
    return dag_orchestrator.list_pipelines()


class ExecuteDAGRequest(BaseModel):
    custom_params: Optional[Dict[str, Any]] = None


@app.post("/api/dag/execute/{pipeline_id}", response_model=DAGExecutionRun)
async def execute_dag_pipeline(pipeline_id: str, req: Optional[ExecuteDAGRequest] = None):
    try:
        custom_params = req.custom_params if req else None
        run = await dag_orchestrator.execute_pipeline(pipeline_id, custom_params=custom_params)
        db.save_dag_run(
            run_id=run.run_id,
            pipeline_id=run.pipeline_id,
            status=run.status.value,
            duration_ms=run.total_duration_ms,
            created_at=run.created_at,
            completed_at=run.completed_at,
            logs=run.execution_logs
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/dag/runs")
def list_dag_run_history():
    return db.list_dag_runs()


# --- Natural Language EDI Query Engine (Hamza's EDI Inspired) ---
@app.post("/api/edi/query", response_model=EDIQueryResponse)
def query_edi_engine(req: EDIQueryRequest):
    return edi_engine.query(req)


@app.get("/api/edi/sheet", response_model=SpreadsheetData)
def get_edi_spreadsheet():
    return edi_engine.get_spreadsheet_data()


@app.post("/api/edi/sheet/update")
def update_edi_cell(req: SpreadsheetCellUpdate):
    success = edi_engine.update_cell(req.ticker, req.column, req.value)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update cell")
    return {"status": "updated", "ticker": req.ticker, "column": req.column, "value": req.value}


@app.get("/api/edi/chart", response_model=ChartSpec)
def get_edi_chart(chart_type: str = Query("BAR", pattern="^(BAR|LINE|AREA|RADAR)$")):
    return edi_engine.generate_chart_spec(chart_type=chart_type)


# --- Arlo-Style Web Scraping Automation Worker Telemetry ---
@app.get("/api/crawler/workers")
def get_crawler_workers():
    return [
        {"worker_id": "worker-us-east-1", "region": "US-East (N. Virginia)", "type": "Headless Chromium", "latency_ms": 24.2, "status": "ACTIVE", "uptime_pct": 99.85},
        {"worker_id": "worker-eu-west-1", "region": "EU-West (Frankfurt)", "type": "Anti-Bot Residential Proxy", "latency_ms": 38.6, "status": "ACTIVE", "uptime_pct": 100.0},
        {"worker_id": "worker-ap-south-1", "region": "AP-South (Mumbai)", "type": "SEC EDGAR Stream Ingester", "latency_ms": 18.1, "status": "ACTIVE", "uptime_pct": 99.92}
    ]


class ScrapeToSheetRequest(BaseModel):
    url: str


@app.post("/api/crawler/scrape-to-sheet")
async def scrape_and_load_into_sheet(req: ScrapeToSheetRequest):
    # Crawl target
    crawl_req = CrawlRequest(url=req.url, user_agent_mode="desktop_chrome")
    crawl_res = await crawler_engine.crawl(crawl_req)
    # Prune DOM
    prune_res = pruner_engine.prune_and_convert(
        raw_html=crawler_engine.MOCK_DOMAINS.get(req.url, "<html><body>SEC Ingested</body></html>")
    )
    # Link entities
    ner_res = linker_engine.extract_and_link(prune_res.markdown_content)
    # Refresh spreadsheet
    sheet = edi_engine.get_spreadsheet_data()
    return {
        "status": "success",
        "scraped_url": req.url,
        "raw_bytes": crawl_res.raw_html_length,
        "cleaned_bytes": prune_res.cleaned_char_count,
        "compression_pct": prune_res.compression_ratio_pct,
        "entities_extracted": ner_res.total_mentions,
        "sheet_total_rows": sheet.total_rows
    }


# --- Mount Static Frontend ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
