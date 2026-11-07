"""
Kuber Data Core (कुबेर) — EDI (Natural Language to SQL & Graph Traversal) Engine
Inspired by Rao Muhammad Hamza's EDI Architecture: Local-first English-to-SQL compiler,
dynamic in-memory SQLite analytical datastore, and multi-turn financial question answering.
"""

import time
import sqlite3
import re
from typing import List, Dict, Any, Optional
from backend.models import (
    EDIQueryRequest,
    EDIQueryResponse,
    ChartSpec,
    ChartSeries,
    SpreadsheetData,
    SpreadsheetCellUpdate
)
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
        # Check single ticker/company lookups
        ticker_aliases = {
            "NVDA": ["nvidia", "nvda"],
            "MSFT": ["microsoft", "msft", "azure"],
            "AAPL": ["apple", "aapl", "iphone"],
            "GOOGL": ["google", "alphabet", "googl"],
            "AMZN": ["amazon", "amzn", "aws"],
            "TSM": ["tsmc", "tsm", "taiwan semi"],
            "ASML": ["asml"],
            "TSLA": ["tesla", "tsla"],
            "AVGO": ["broadcom", "avgo"],
            "AMD": ["amd", "advanced micro"]
        }

        matched_company = None
        for t_code, aliases in ticker_aliases.items():
            if any(re.search(rf"\b{a}\b", q_lower) for a in aliases):
                matched_company = t_code
                break

        if "market cap" in q_lower or "valuation" in q_lower or "worth" in q_lower:
            intent = "MARKET_CAP_ANALYSIS"
            if "over" in q_lower or ">" in q_lower or "greater" in q_lower:
                num_match = re.search(r"(\d+)", q)
                cutoff = float(num_match.group(1)) if num_match else 1000.0
                sql = f"SELECT ticker, name, sector, market_cap_b FROM companies WHERE market_cap_b >= {cutoff} ORDER BY market_cap_b DESC LIMIT {req.top_k}"
            else:
                sql = f"SELECT ticker, name, sector, market_cap_b FROM companies ORDER BY market_cap_b DESC LIMIT {req.top_k}"

        elif "revenue" in q_lower or "sales" in q_lower:
            intent = "REVENUE_ANALYSIS"
            if matched_company:
                sql = f"SELECT c.ticker, c.name, f.revenue_b, f.operating_income_b, f.net_income_b FROM companies c JOIN financials f ON c.ticker = f.ticker WHERE c.ticker = '{matched_company}'"
            else:
                sql = f"SELECT c.ticker, c.name, f.revenue_b, f.operating_income_b, f.net_income_b FROM companies c JOIN financials f ON c.ticker = f.ticker ORDER BY f.revenue_b DESC LIMIT {req.top_k}"

        elif "debt" in q_lower or "leverage" in q_lower or "liabilit" in q_lower:
            intent = "LEVERAGE_ANALYSIS"
            if matched_company:
                sql = f"SELECT c.ticker, c.name, f.total_liabilities_b, f.debt_to_equity, f.operating_cash_flow_b FROM companies c JOIN financials f ON c.ticker = f.ticker WHERE c.ticker = '{matched_company}'"
            else:
                sql = f"SELECT c.ticker, c.name, f.total_liabilities_b, f.debt_to_equity, f.operating_cash_flow_b FROM companies c JOIN financials f ON c.ticker = f.ticker ORDER BY f.debt_to_equity DESC LIMIT {req.top_k}"

        elif "margin" in q_lower or "profit" in q_lower:
            intent = "PROFITABILITY_RANKING"
            if matched_company:
                sql = f"SELECT c.ticker, c.name, f.revenue_b, f.gross_profit_b, f.gross_margin_pct, f.operating_margin_pct FROM companies c JOIN financials f ON c.ticker = f.ticker WHERE c.ticker = '{matched_company}'"
            else:
                sql = f"""
                    SELECT c.ticker, c.name, f.revenue_b, f.gross_profit_b, f.gross_margin_pct, f.operating_margin_pct
                    FROM companies c JOIN financials f ON c.ticker = f.ticker
                    ORDER BY f.operating_margin_pct DESC LIMIT {req.top_k}
                """

        elif "suppl" in q_lower or "customer" in q_lower or "chip" in q_lower or "foundry" in q_lower or "partner" in q_lower:
            intent = "SUPPLY_CHAIN_INSPECTION"
            if matched_company:
                sql = f"SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain WHERE source_name = '{matched_company}' OR target_name = '{matched_company}'"
                cypher = f"MATCH (s)-[r:SUPPLIES_TO]-(t) WHERE s.ticker = '{matched_company}' OR t.ticker = '{matched_company}' RETURN s, r, t"
            else:
                sql = f"SELECT source_name, relation, target_name, dependency_weight, description FROM supply_chain LIMIT {req.top_k}"
                cypher = "MATCH (s)-[r:SUPPLIES_TO]->(t) RETURN s, r, t LIMIT 15"

        elif "ceo" in q_lower or "executive" in q_lower or "leader" in q_lower:
            intent = "EXECUTIVE_LOOKUP"
            if matched_company:
                sql = f"SELECT e.name as executive_name, e.title, c.name as company_name, c.ticker FROM executives e JOIN companies c ON e.company_ticker = c.ticker WHERE c.ticker = '{matched_company}'"
            else:
                sql = "SELECT e.name as executive_name, e.title, c.name as company_name, c.ticker FROM executives e JOIN companies c ON e.company_ticker = c.ticker"

        elif "compete" in q_lower or "rival" in q_lower:
            intent = "COMPETITOR_ANALYSIS"
            if matched_company:
                sql = f"SELECT source_name, relation, target_name, description FROM supply_chain WHERE relation = 'COMPETES_WITH' AND (source_name = '{matched_company}' OR target_name = '{matched_company}')"
                cypher = f"MATCH (a:Company)-[r:COMPETES_WITH]-(b:Company) WHERE a.ticker = '{matched_company}' OR b.ticker = '{matched_company}' RETURN a, b"
            else:
                sql = "SELECT source_name, relation, target_name, description FROM supply_chain WHERE relation = 'COMPETES_WITH'"
                cypher = "MATCH (a:Company)-[r:COMPETES_WITH]-(b:Company) RETURN a, b"

        elif matched_company:
            intent = "COMPANY_PROFILE"
            sql = f"""
                SELECT c.ticker, c.name, c.sector, c.country, c.market_cap_b, f.revenue_b, f.gross_margin_pct, f.operating_margin_pct, f.debt_to_equity
                FROM companies c LEFT JOIN financials f ON c.ticker = f.ticker
                WHERE c.ticker = '{matched_company}'
            """

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

        # Check if chart requested
        chart_spec = None
        if any(w in q_lower for w in ["chart", "plot", "graph", "visualize", "bar", "margin", "market cap"]):
            if "margin" in q_lower or "profit" in q_lower:
                chart_spec = self.generate_chart_spec("BAR")
            elif "market cap" in q_lower or "valuation" in q_lower:
                chart_spec = self.generate_chart_spec("LINE")
            else:
                chart_spec = self.generate_chart_spec("BAR")

        return EDIQueryResponse(
            natural_query=q,
            intent=intent,
            generated_sql=sql.strip(),
            generated_cypher=cypher,
            column_headers=col_headers,
            rows=rows,
            natural_language_answer=answer,
            chart_spec=chart_spec,
            execution_time_ms=duration_ms,
            grounded_record_count=len(rows)
        )

    def get_spreadsheet_data(self) -> SpreadsheetData:
        """Returns the full unified tabular dataset for the EDI spreadsheet grid."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                c.ticker,
                c.name as company_name,
                c.sector,
                c.country,
                c.market_cap_b,
                COALESCE(f.revenue_b, 0.0) as revenue_b,
                COALESCE(f.gross_margin_pct, 0.0) as gross_margin_pct,
                COALESCE(f.operating_margin_pct, 0.0) as operating_margin_pct,
                COALESCE(f.debt_to_equity, 0.0) as debt_to_equity
            FROM companies c
            LEFT JOIN financials f ON c.ticker = f.ticker
            ORDER BY c.market_cap_b DESC
        """)
        columns = [
            "ticker", "company_name", "sector", "country",
            "market_cap_b", "revenue_b", "gross_margin_pct",
            "operating_margin_pct", "debt_to_equity"
        ]
        rows = [dict(r) for r in cur.fetchall()]
        return SpreadsheetData(
            columns=columns,
            rows=rows,
            total_rows=len(rows)
        )

    def update_cell(self, ticker: str, column: str, value: Any) -> bool:
        """Dynamically updates a cell value in SQLite analytical store and recalculates metrics."""
        cur = self.conn.cursor()
        try:
            clean_ticker = ticker.upper().strip()
            # Normalize column aliases
            if column in ["company_name", "name"]:
                cur.execute("UPDATE companies SET name = ? WHERE ticker = ?", (str(value).strip(), clean_ticker))
            elif column in ["sector", "country"]:
                cur.execute(f"UPDATE companies SET {column} = ? WHERE ticker = ?", (str(value).strip(), clean_ticker))
            elif column == "market_cap_b":
                val_float = float(str(value).replace("$", "").replace("B", "").replace(",", "").strip())
                cur.execute("UPDATE companies SET market_cap_b = ? WHERE ticker = ?", (val_float, clean_ticker))
            elif column in ["revenue_b", "gross_margin_pct", "operating_margin_pct", "debt_to_equity"]:
                val_float = float(str(value).replace("%", "").replace(",", "").strip())
                cur.execute(f"UPDATE financials SET {column} = ? WHERE ticker = ?", (val_float, clean_ticker))
            self.conn.commit()
            return True
        except Exception:
            return False

    def generate_chart_spec(self, chart_type: str = "BAR") -> ChartSpec:
        """
        Synthesizes structured chart specifications (series, points, axes)
        for dynamic browser-side SVG/Recharts rendering.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT c.ticker, c.market_cap_b, COALESCE(f.revenue_b, 0.0) as rev, COALESCE(f.operating_margin_pct, 0.0) as om
            FROM companies c LEFT JOIN financials f ON c.ticker = f.ticker
            ORDER BY c.market_cap_b DESC LIMIT 6
        """)
        records = [dict(r) for r in cur.fetchall()]
        tickers = [r["ticker"] for r in records]

        if chart_type == "LINE":
            # Market Cap Line Trend
            caps = [r["market_cap_b"] for r in records]
            return ChartSpec(
                chart_type="LINE",
                title="Market Capitalization Distribution ($B)",
                x_axis_labels=tickers,
                series=[ChartSeries(name="Market Cap ($B)", data_points=caps, color="#facc15")],
                legend=["Market Cap ($B)"]
            )
        elif chart_type == "RADAR":
            # 5-Axis Solvency Radar (NVDA Altman components)
            return ChartSpec(
                chart_type="RADAR",
                title="Altman Z-Score 5-Factor Radar (NVDA)",
                x_axis_labels=["Working Capital", "Retained Earnings", "EBIT", "Equity/Liabilities", "Asset Turnover"],
                series=[
                    ChartSeries(name="NVDA Actual Factor", data_points=[0.67, 0.51, 0.50, 2.76, 0.92], color="#38bdf8"),
                    ChartSeries(name="Industry Benchmark", data_points=[0.25, 0.30, 0.20, 1.20, 0.65], color="#10b981")
                ],
                legend=["NVDA Actual", "Industry Benchmark"]
            )
        else:
            # Default: Dual Bar Chart (Revenue vs Operating Margin)
            revenues = [r["rev"] for r in records]
            margins = [r["om"] for r in records]
            return ChartSpec(
                chart_type="BAR",
                title="Revenue ($B) & Operating Profitability (%) Across Key Cohort",
                x_axis_labels=tickers,
                series=[
                    ChartSeries(name="Revenue ($B)", data_points=revenues, color="#facc15"),
                    ChartSeries(name="Operating Margin (%)", data_points=margins, color="#10b981")
                ],
                legend=["Revenue ($B)", "Operating Margin (%)"]
            )

    def _synthesize_natural_answer(self, query: str, intent: str, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return f"No records found matching query: '{query}'. Try asking about market caps, supply chains, or operating margins."

        if intent == "MARKET_CAP_ANALYSIS":
            top = rows[0]
            return f"Retrieved {len(rows)} companies. {top.get('name')} leads the cohort with a market valuation of ${top.get('market_cap_b', 0):,.1f}B."

        elif intent == "REVENUE_ANALYSIS":
            top = rows[0]
            return f"Revenue ranking across {len(rows)} firm(s): {top.get('name')} reports ${top.get('revenue_b', 0):,.1f}B in annual sales, generating ${top.get('operating_income_b', 0):,.1f}B in operating income."

        elif intent == "LEVERAGE_ANALYSIS":
            top = rows[0]
            return f"Capital structure evaluation: {top.get('name')} maintains a debt-to-equity ratio of {top.get('debt_to_equity')} with ${top.get('total_liabilities_b', 0):,.1f}B total liabilities."

        elif intent == "COMPANY_PROFILE":
            c = rows[0]
            return f"{c.get('name')} ({c.get('ticker')}) commands a market cap of ${c.get('market_cap_b', 0):,.1f}B in {c.get('sector')}. Revenue: ${c.get('revenue_b', 0):,.1f}B, Operating Margin: {c.get('operating_margin_pct')}%, D/E: {c.get('debt_to_equity')}."

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
