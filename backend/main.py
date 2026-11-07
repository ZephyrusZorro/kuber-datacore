"""
Kuber Data Core (कुबेर) — Main FastAPI Application
Autonomous Distributed Web Intelligence, Financial Knowledge Graph & Market Cortex Service.
"""

import sys
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import (
    CrawlRequest,
    CrawlResponse,
    FilterStrategy,
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
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
from backend.web_crawler import CrawlFetchError, WebCrawlerEngine
from backend.dom_pruner import DOMPruningEngine
from backend.entity_linker import EntityLinkingEngine
from backend.knowledge_graph import KnowledgeGraphEngine
from backend.financial_ratios import FinancialRatioEngine
from backend.dag_orchestrator import DAGOrchestrator
from backend.edi_query_engine import EDIQueryEngine
from backend.sample_market_data import MARKET_TICKERS
from backend.db import KuberDatabase



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with WebCrawlerEngine.create_client() as client:
        yield {"crawler": WebCrawlerEngine(client)}


app = FastAPI(
    title="Kuber Data Core (कुबेर)",
    description="Autonomous Web Intelligence, Financial Knowledge Graph & Market Cortex Pipeline",
    version="1.0.0",
    lifespan=lifespan,
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


# --- Favicon ---
@app.get("/favicon.ico", include_in_schema=False)
def get_favicon():
    svg_favicon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <rect width="100" height="100" rx="24" fill="#35212a"/>
      <path d="M50 19 77 35v31L50 82 23 66V35l27-16Zm0 63V50m0 0 27-15M50 50 23 35"
        fill="none" stroke="#f0cbb3" stroke-linejoin="round" stroke-width="4"/>
    </svg>"""
    return Response(content=svg_favicon, media_type="image/svg+xml")


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
def get_request_crawler(request: Request) -> WebCrawlerEngine:
    return getattr(request.state, "crawler", crawler_engine)


async def fetch_document(req: CrawlRequest, request: Request) -> CrawlResponse:
    try:
        return await get_request_crawler(request).crawl(req)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except CrawlFetchError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def analyze_document(crawl: CrawlResponse, req: DocumentAnalysisRequest, persist: bool) -> DocumentAnalysisResponse:
    document = pruner_engine.prune_and_convert(
        raw_html=crawl.raw_html, strategy=req.strategy, query_context=req.query_context
    )
    analysis = DocumentAnalysisResponse(provenance=crawl, document=document)
    if req.include_entities:
        matches = linker_engine.extract_and_link(document.markdown_content)
        analysis.entity_mentions = matches.total_mentions
        analysis.entity_names = list(dict.fromkeys(mention.matched_canonical.name for mention in matches.mentions))
    if persist:
        db.save_crawled_doc(
            url=crawl.url,
            title=crawl.title,
            status_code=crawl.status_code,
            raw_length=crawl.raw_html_length,
            cleaned_length=document.cleaned_char_count,
            compression_ratio=document.compression_ratio_pct,
            markdown_preview=document.markdown_content,
            crawled_at=crawl.crawled_at,
        )
    return analysis


@app.post("/api/crawler/analyze", response_model=DocumentAnalysisResponse)
async def analyze_source(req: DocumentAnalysisRequest, request: Request):
    crawl = await fetch_document(req, request)
    return await run_in_threadpool(analyze_document, crawl, req, persist=True)


@app.post("/api/crawler/crawl", response_model=CrawlResponse)
async def crawl_web_page(req: CrawlRequest, request: Request):
    crawl = await fetch_document(req, request)
    analysis_request = DocumentAnalysisRequest(url=req.url)
    await run_in_threadpool(analyze_document, crawl, analysis_request, persist=True)
    return crawl


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
    kg_engine.add_relations(res.relations)
    return res


# --- Knowledge Graph Endpoints ---
@app.get("/api/graph/view", response_model=KnowledgeGraphView)
def get_graph_view():
    return Response(kg_engine.get_view_json(), media_type="application/json")


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
    try:
        return ratio_engine.generate_valuation_report(ticker)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
async def execute_dag_pipeline(pipeline_id: str, request: Request, req: Optional[ExecuteDAGRequest] = None):
    try:
        custom_params = req.custom_params if req else None
        run = await dag_orchestrator.execute_pipeline(
            pipeline_id, custom_params=custom_params, crawler=get_request_crawler(request)
        )
        await run_in_threadpool(
            db.save_dag_run,
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
    strategy: FilterStrategy = FilterStrategy.PRUNING_LXML
    query_context: Optional[str] = None


@app.post("/api/crawler/scrape-to-sheet")
async def scrape_and_load_into_sheet(req: ScrapeToSheetRequest, request: Request):
    analysis_request = DocumentAnalysisRequest(
        url=req.url, strategy=req.strategy, query_context=req.query_context, include_entities=True
    )
    crawl = await fetch_document(analysis_request, request)
    result = await run_in_threadpool(analyze_document, crawl, analysis_request, persist=False)
    sheet = await run_in_threadpool(edi_engine.get_spreadsheet_data)
    return {
        "status": "success",
        "scraped_url": req.url,
        "raw_bytes": crawl.raw_html_length,
        "cleaned_bytes": result.document.cleaned_char_count,
        "compression_pct": result.document.compression_ratio_pct,
        "entities_extracted": result.entity_mentions,
        "sheet_total_rows": sheet.total_rows,
        "source": crawl.source,
        "markdown_content": result.document.markdown_content,
        "entities": result.entity_names,
        "chunks": result.document.chunks,
    }


# --- Mount Static Frontend ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
