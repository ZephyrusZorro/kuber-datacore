"""
Kuber Data Core (कुबेर) — EDI (Natural Language to SQL & Graph Traversal) Engine
Inspired by Rao Muhammad Hamza's EDI Architecture: Local-first English-to-SQL compiler,
dynamic in-memory SQLite analytical datastore, and multi-turn financial question answering.
"""

import time
import sqlite3
import re
from typing import List, Dict, Any, Optional
from backend.models import EDIQueryRequest, EDIQueryResponse
from backend.sample_market_data import (
    CANONICAL_COMPANIES,
    CANONICAL_EXECUTIVES,
    CANONICAL_RELATIONSHIPS,
    FINANCIAL_RECORDS
)


class EDIQueryEngine:
    """
    EDI (Enterprise Data Intelligence) ReAct & SQL Synthesis Engine.
    Translates natural language questions into executable SQL & Graph traversals.
    """

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_sqlite_tables()

    def _init_sqlite_tables(self) -> None:
        """Constructs and populates analytical relational tables."""
        cur = self.conn.cursor()

        # Table 1: Companies
        cur.execute("""
            CREATE TABLE companies (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT NOT NULL,
                country TEXT NOT NULL,
                market_cap_b REAL NOT NULL,
                cik TEXT
            )
        """)

        # Table 2: Financial Metrics
        cur.execute("""
            CREATE TABLE financials (
                ticker TEXT PRIMARY KEY,
                revenue_b REAL,
                gross_profit_b REAL,
                operating_income_b REAL,
                net_income_b REAL,
                total_assets_b REAL,
                total_liabilities_b REAL,
                operating_cash_flow_b REAL,
                gross_margin_pct REAL,
                operating_margin_pct REAL,
                debt_to_equity REAL,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            )
        """)

        # Table 3: Supply Chain & Strategic Relationships
        cur.execute("""
            CREATE TABLE supply_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                source_name TEXT NOT NULL,
                target_name TEXT NOT NULL,
                relation TEXT NOT NULL,
                dependency_weight REAL,
                description TEXT
            )
        """)

        # Table 4: Executives
        cur.execute("""
            CREATE TABLE executives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_ticker TEXT,
                title TEXT NOT NULL
            )
        """)

        # Seed Companies
        for c in CANONICAL_COMPANIES.values():
            cur.execute(
                "INSERT INTO companies VALUES (?, ?, ?, ?, ?, ?)",
                (c.ticker, c.name, c.sector, c.country, c.market_cap_billions or 0.0, c.cik)
            )

        # Seed Financials
        for f in FINANCIAL_RECORDS.values():
            rev = max(0.01, f.revenue_billions)
            equity = max(0.01, f.total_assets_billions - f.total_liabilities_billions)
            gm = round((f.gross_profit_billions / rev) * 100.0, 2)
            om = round((f.operating_income_ebit_billions / rev) * 100.0, 2)
            de = round(f.total_liabilities_billions / equity, 2)

            cur.execute(
                "INSERT INTO financials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f.ticker, f.revenue_billions, f.gross_profit_billions,
                    f.operating_income_ebit_billions, f.net_income_billions,
                    f.total_assets_billions, f.total_liabilities_billions,
                    f.operating_cash_flow_billions, gm, om, de
                )
            )

        # Seed Relationships
        for r in CANONICAL_RELATIONSHIPS:
            src_name = r["source"].replace("company-", "").replace("exec-", "").upper()
            tgt_name = r["target"].replace("company-", "").replace("exec-", "").upper()
            cur.execute(
                "INSERT INTO supply_chain (source_id, target_id, source_name, target_name, relation, dependency_weight, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (r["source"], r["target"], src_name, tgt_name, r["relation"].value, r["weight"], r["desc"])
            )

        # Seed Executives
        exec_map = [
            ("Jensen Huang", "NVDA", "President, Founder & CEO"),
            ("Satya Nadella", "MSFT", "Chairman & CEO"),
            ("Tim Cook", "AAPL", "CEO"),
            ("Sundar Pichai", "GOOGL", "CEO Alphabet & Google"),
            ("Andy Jassy", "AMZN", "President & CEO"),
            ("Lisa Su", "AMD", "Chair & CEO"),
            ("Elon Musk", "TSLA", "Technoking & CEO")
        ]
        for name, tick, title in exec_map:
            cur.execute("INSERT INTO executives (name, company_ticker, title) VALUES (?, ?, ?)", (name, tick, title))

        self.conn.commit()

    def query(self, req: EDIQueryRequest) -> EDIQueryResponse:
        start_time = time.perf_counter()
        q = req.natural_query.strip()
        q_lower = q.lower()

        sql = ""
        intent = "GENERAL_QUERY"
        cypher = None

        # Rule-based NL-to-SQL Compiler
        if "market cap" in q_lower or "valuation" in q_lower or "worth" in q_lower:
            intent = "MARKET_CAP_ANALYSIS"
            if "over" in q_lower or ">" in q_lower or "greater" in q_lower:
                num_match = re.search(r"(\d+)", q)
                cutoff = float(num_match.group(1)) if num_match else 1000.0
                sql = f"SELECT ticker, name, sector, market_cap_b FROM companies WHERE market_cap_b >= {cutoff} ORDER BY market_cap_b DESC LIMIT {req.top_k}"
            else:
                sql = f"SELECT ticker, name, sector, market_cap_b FROM companies ORDER BY market_cap_b DESC LIMIT {req.top_k}"

        elif "margin" in q_lower or "profit" in q_lower:
            intent = "PROFITABILITY_RANKING"
            sql = f"""
                SELECT c.ticker, c.name, f.revenue_b, f.gross_profit_b, f.gross_margin_pct, f.operating_margin_pct
                FROM companies c JOIN financials f ON c.ticker = f.ticker
                ORDER BY f.operating_margin_pct DESC LIMIT {req.top_k}
            """

        elif "suppl" in q_lower or "customer" in q_lower or "chip" in q_lower or "foundry" in q_lower or "partner" in q_lower:
            intent = "SUPPLY_CHAIN_INSPECTION"
            if "tsmc" in q_lower or "tsm" in q_lower:
                sql = "SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain WHERE source_name = 'TSM' OR target_name = 'TSM'"
                cypher = "MATCH (s:Company {ticker: 'TSM'})-[r:SUPPLIES_TO]->(t:Company) RETURN s, r, t"
            elif "nvda" in q_lower or "nvidia" in q_lower:
                sql = "SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain WHERE source_name = 'NVDA' OR target_name = 'NVDA'"
                cypher = "MATCH (s:Company)-[r:SUPPLIES_TO]->(t:Company {ticker: 'NVDA'}) RETURN s, r, t"
            elif "asml" in q_lower:
                sql = "SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain WHERE source_name = 'ASML' OR target_name = 'ASML'"
                cypher = "MATCH (s:Company {ticker: 'ASML'})-[r:SUPPLIES_TO]->(t:Company) RETURN s, r, t"
            else:
                sql = f"SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain LIMIT {req.top_k}"
                cypher = "MATCH (s)-[r:SUPPLIES_TO]->(t) RETURN s, r, t LIMIT 15"

        elif "ceo" in q_lower or "executive" in q_lower or "leader" in q_lower:
            intent = "EXECUTIVE_LOOKUP"
            sql = "SELECT e.name as executive_name, e.title, c.name as company_name, c.ticker FROM executives e JOIN companies c ON e.company_ticker = c.ticker"

        elif "compete" in q_lower or "rival" in q_lower:
            intent = "COMPETITOR_ANALYSIS"
            sql = "SELECT source_name, relation, target_name, description FROM supply_chain WHERE relation = 'COMPETES_WITH'"
            cypher = "MATCH (a:Company)-[r:COMPETES_WITH]-(b:Company) RETURN a, b"

        else:
            intent = "DEFAULT_OVERVIEW"
            sql = f"""
                SELECT c.ticker, c.name, c.sector, c.market_cap_b, f.revenue_b, f.operating_margin_pct
                FROM companies c LEFT JOIN financials f ON c.ticker = f.ticker
                ORDER BY c.market_cap_b DESC LIMIT {req.top_k}
            """

        # Execute synthesized SQL
        rows: List[Dict[str, Any]] = []
        col_headers: List[str] = []
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            col_headers = [desc[0] for desc in cur.description] if cur.description else []
            for r in cur.fetchall():
                rows.append(dict(r))
        except Exception as err:
            sql = f"-- Error executing query: {str(err)}"
            rows = []

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Synthesize plain English response
        answer = self._synthesize_natural_answer(q, intent, rows)

        return EDIQueryResponse(
            natural_query=q,
            intent=intent,
            generated_sql=sql.strip(),
            generated_cypher=cypher,
            column_headers=col_headers,
            rows=rows,
            natural_language_answer=answer,
            execution_time_ms=duration_ms,
            grounded_record_count=len(rows)
        )

    def _synthesize_natural_answer(self, query: str, intent: str, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return f"No records found matching query: '{query}'. Try asking about market caps, supply chains, or operating margins."

        if intent == "MARKET_CAP_ANALYSIS":
            top = rows[0]
            return f"Retrieved {len(rows)} companies. {top.get('name')} leads the cohort with a market valuation of ${top.get('market_cap_b', 0):,.1f}B."

        elif intent == "PROFITABILITY_RANKING":
            leader = rows[0]
            return f"Operating margin analysis across {len(rows)} reporting firms: {leader.get('name')} ({leader.get('ticker')}) commands the highest operating profitability at {leader.get('operating_margin_pct')}%, on annual revenue of ${leader.get('revenue_b')}B."

        elif intent == "SUPPLY_CHAIN_INSPECTION":
            return f"Found {len(rows)} active supply chain and manufacturing interconnections. Key pathways demonstrate single-source lithography and foundry dependencies across top compute producers."

        elif intent == "EXECUTIVE_LOOKUP":
            names = [f"{r.get('executive_name')} ({r.get('company_name')})" for r in rows[:4]]
            return f"Identified key leadership: {', '.join(names)}, managing strategic corporate governance."

        elif intent == "COMPETITOR_ANALYSIS":
            return f"Identified {len(rows)} strategic rivalries, spanning enterprise cloud (Azure vs AWS), mobile operating systems (iOS vs Android), and AI silicon (Nvidia vs AMD)."

        return f"Query returned {len(rows)} grounded analytical records from Kuber Data Core."
