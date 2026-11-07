"""Compare Kuber architecture paths on a controlled HTTP source and sample graph."""

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import statistics
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from time import perf_counter, sleep

import httpx
import uvicorn

sys.path.insert(0, str(Path.cwd()))
from backend import main
from backend.db import KuberDatabase


REPORT = (
    "<html><head><title>Benchmark filing</title></head><body>"
    "<nav><a href='/'>Home</a></nav><main><h1>Financial statement</h1>"
    + "".join(
        f"<section><h2>Segment {index}</h2>"
        "<p>Revenue increased across cloud and enterprise software operations.</p>"
        "<table><tr><th>Metric</th><th>Value</th></tr>"
        "<tr><td>Operating cash flow</td><td>125</td></tr>"
        "<tr><td>Sales</td><td>291</td></tr></table></section>"
        for index in range(400)
    )
    + "</main></body></html>"
).encode()


class FilingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def do_GET(self):
        self.server.connections.add(self.client_address)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(REPORT)))
        self.end_headers()
        self.wfile.write(REPORT)

    def log_message(self, *args):
        pass


def latency(samples):
    ordered = sorted(samples)
    return {
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[(95 * len(ordered) + 99) // 100 - 1], 3),
    }


def measure(client, source, legacy, count):
    def extract():
        if legacy:
            crawl = client.post("/api/crawler/crawl", json={"url": source}).raise_for_status()
            request = json.dumps({"raw_html": crawl.json()["raw_html"]})
            prune = client.post("/api/crawler/prune", content=request, headers={"Content-Type": "application/json"}).raise_for_status()
            return prune.json()["markdown_content"], len(crawl.content) + len(prune.content) + len(request)
        result = client.post("/api/crawler/analyze", json={"url": source}).raise_for_status()
        return result.json()["document"]["markdown_content"], len(result.content)

    graph = client.get("/api/graph/view").raise_for_status().json()
    extract()
    source_samples, graph_samples = [], []
    markdown, bytes_moved = "", 0
    for _ in range(count):
        start = perf_counter()
        markdown, bytes_moved = extract()
        source_samples.append((perf_counter() - start) * 1000)
        start = perf_counter()
        assert client.get("/api/graph/view").raise_for_status().json() == graph
        graph_samples.append((perf_counter() - start) * 1000)

    return {
        "mode": "legacy" if legacy else "single-pass",
        "samples": count,
        "source": {
            **latency(source_samples),
            "browser_requests": 2 if legacy else 1,
            "body_bytes": bytes_moved,
            "markdown_sha256": hashlib.sha256(markdown.encode()).hexdigest(),
        },
        "graph": {
            **latency(graph_samples),
            "snapshot_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest(),
        },
    }


def run(legacy, samples):
    with TemporaryDirectory(prefix="kuber-bench-") as directory, socket.socket() as listener, ThreadingHTTPServer(
        ("127.0.0.1", 0), FilingHandler
    ) as provider:
        main.db = KuberDatabase(Path(directory) / "bench.db")
        provider.connections = set()
        upstream = Thread(target=provider.serve_forever, daemon=True)
        upstream.start()
        listener.bind(("127.0.0.1", 0))
        service = uvicorn.Server(uvicorn.Config(main.app, log_level="warning"))
        server = Thread(target=service.run, kwargs={"sockets": [listener]}, daemon=True)
        server.start()
        try:
            for _ in range(100):
                if service.started:
                    break
                sleep(0.05)
            if not service.started:
                raise RuntimeError("Kuber did not start")
            with httpx.Client(base_url=f"http://127.0.0.1:{listener.getsockname()[1]}", timeout=30) as client:
                results = measure(client, f"http://127.0.0.1:{provider.server_port}/report", legacy, samples)
            results["source"]["upstream_connections_including_warmup"] = len(provider.connections)
            print(json.dumps(results, indent=2))
        finally:
            service.should_exit = True
            server.join(timeout=10)
            provider.shutdown()
            upstream.join(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", action="store_true", help="Use the old crawl and prune endpoints")
    parser.add_argument("--samples", type=int, default=30)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    run(args.legacy, args.samples)
