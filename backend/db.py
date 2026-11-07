"""
Kuber Data Core (कुबेर) — SQLite Persistence Layer
Stores crawled web documents, extracted entities, DAG execution logs, and graph snapshots.
"""

import sqlite3
import json
from contextlib import closing, contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "kuber.db"


class KuberDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.row_factory = sqlite3.Row
            yield conn

    def _init_db(self) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crawled_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    status_code INTEGER,
                    raw_length INTEGER,
                    cleaned_length INTEGER,
                    compression_ratio REAL,
                    markdown_preview TEXT,
                    crawled_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dag_runs (
                    run_id TEXT PRIMARY KEY,
                    pipeline_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    logs_json TEXT
                )
            """)

    def save_crawled_doc(
        self,
        url: str,
        title: str,
        status_code: int,
        raw_length: int,
        cleaned_length: int,
        compression_ratio: float,
        markdown_preview: str,
        crawled_at: str
    ) -> int:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO crawled_documents 
                (url, title, status_code, raw_length, cleaned_length, compression_ratio, markdown_preview, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (url, title, status_code, raw_length, cleaned_length, compression_ratio, markdown_preview[:2000], crawled_at))
            return cur.lastrowid

    def list_crawled_docs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crawled_documents ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def save_dag_run(
        self,
        run_id: str,
        pipeline_id: str,
        status: str,
        duration_ms: float,
        created_at: str,
        completed_at: Optional[str],
        logs: List[str]
    ) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO dag_runs
                (run_id, pipeline_id, status, duration_ms, created_at, completed_at, logs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, pipeline_id, status, duration_ms, created_at, completed_at, json.dumps(logs)))

    def list_dag_runs(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM dag_runs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = []
            for r in cur.fetchall():
                d = dict(r)
                d["logs"] = json.loads(d["logs_json"]) if d.get("logs_json") else []
                rows.append(d)
            return rows
