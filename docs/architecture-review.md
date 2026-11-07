# Kuber architecture review

Kuber runs as a local financial research workstation with a small editable dataset, a document ingestion path, a relationship graph, and preset analysis pipelines. This review compared patterns that improve those workflows on a single machine. GitHub and project documentation establish how the alternatives work. Reddit threads capture practitioner experiences and helped identify tradeoffs to test locally.

## Patterns reviewed

| Project or source | Pattern | Decision for Kuber |
| --- | --- | --- |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) and its [provider architecture](https://docs.openbb.co/odp/python/concepts/architecture) | Validate the request, retrieve the source, and transform it into typed data. | Adopt one typed Source lab workflow that returns provenance, Markdown, chunks, and optional entity matches. |
| [Scrapy](https://github.com/scrapy/scrapy), [download limits](https://docs.scrapy.org/en/master/topics/security.html), and [HTTPX async clients](https://www.python-httpx.org/async/) | Reuse connections and cap document reads. | Use one pool per FastAPI lifespan, a total download deadline, five redirects, and 4 MiB limits on wire and decoded bodies. |
| [Crawl4AI](https://github.com/unclecode/crawl4ai), [Trafilatura](https://github.com/adbar/trafilatura), and [extraction discussion](https://www.reddit.com/r/webscraping/comments/1fqxsoq/) | Browser rendering serves script-driven sites. Article extraction tools emphasize text and boilerplate removal. | Keep the current table-preserving HTML path for the measured workload. A broader parser comparison would need a representative corpus of malformed filings and tables. |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) and [EdgarTools](https://github.com/dgunning/edgartools) | Agent-based research and structured SEC filing ingestion address different workloads. | Keep worksheet and valuation behavior deterministic. An EDGAR provider would be a separate data integration with its own [identity and fair-access requirements](https://www.sec.gov/about/developer-resources). |
| [Prefect](https://github.com/PrefectHQ/prefect/blob/main/docs/v3/concepts/tasks.mdx), [Airflow](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html), and [orchestration discussion](https://www.reddit.com/r/dataengineering/comments/1ltpaxq/) | Track terminal task states and enforce dependencies. | Keep orchestration embedded. Validate the graph before execution, show skipped steps after a failure, and persist run summaries in SQLite. |
| [SQLite guidance](https://sqlite.org/whentouse.html), [DuckDB](https://github.com/duckdb/duckdb), and [embedded database discussion](https://www.reddit.com/r/dataengineering/comments/1eoaq8s/) | Embedded storage supports local workflows. Columnar analytics serves larger scan-heavy datasets. | Keep SQLite for worksheet edits and history. The current dataset fits an embedded transactional engine. |
| [NetworkX PageRank](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html), [D3 force simulation](https://d3js.org/d3-force/simulation), and [canvas rendering discussion](https://www.reddit.com/r/html5/comments/f9xr1m/) | Use weighted power iteration for ranking, then stop drawing when a layout has settled. | Serve a cached graph snapshot until an edit changes it. Let the canvas settle, then redraw on interaction, updates, or shock animation. |

## Data flow and compatibility

`POST /api/crawler/analyze` is the Source lab entry point. It fetches a bundled fixture or HTTP document, applies the chosen extraction strategy once in a worker thread, and returns normalized results with source metadata. Existing crawler, pruning, and entity extraction endpoints remain available. Web fetches negotiate identity or gzip, bound wire and decoded bytes separately, and keep redirect cookies local to each crawl.

Graph mutations invalidate the typed snapshot under a lock. Identical evidence keeps the snapshot warm. The graph endpoint serves its cached JSON, and engine callers receive independent typed objects. Weighted PageRank runs on the existing NetworkX graph and Python runtime. Shock propagation counts each company once using its strongest modeled exposure across up to three hops. The relationship graph is shared for the running session.

Preset pipelines move synchronous processing off the event loop and keep artifacts scoped to their run. SQLite stores run history summaries. Failed runs expose terminal states for their steps.

## Controlled benchmark

Baseline `021c612` and the candidate each ran 30 measured iterations after one warm-up, sequentially on the same Windows host. The loopback server supplied a synthetic filing with 400 sections and tables. The graph measurement used repeated HTTP reads of the bundled sample graph. Byte counts cover HTTP bodies transferred between the UI client and Kuber, excluding headers.

| Metric | Baseline | Candidate |
| --- | ---: | ---: |
| Source extraction median | 431.009 ms | 128.645 ms |
| Source extraction p95 | 447.693 ms | 152.649 ms |
| Source HTTP body bytes | 268,924 | 69,668 |
| Source requests from client | 2 | 1 |
| Upstream TCP connections, including warm-up | 31 | 1 |
| Graph endpoint median | 2.118 ms | 1.062 ms |
| Graph endpoint p95 | 2.322 ms | 1.267 ms |

The extracted Markdown and canonicalized graph JSON matched byte for byte, as checked by SHA-256. In the Edge audit, the idle graph repainted 32 times in a 200 ms sample with reduced motion enabled before the change and zero times afterward. These measurements characterize Kuber on a controlled local workload. Third-party latency and larger production workloads require separate measurements.

Run the current path from the repository root.

```bash
python scripts/benchmark_architecture.py
```

To reproduce the baseline, open a checkout of `021c612` and run the current benchmark script by absolute path with `--legacy`. The script imports Kuber from the working directory.
