"""
Kuber Data Core (कुबेर) — Canonical Market & Enterprise Financial Dataset
High-density financial metrics, SEC CIK registries, multi-tier supply chain relationships,
and corporate executive mapping for global technology and semiconductor ecosystem.
"""

from typing import Dict, List, Any
from backend.models import (
    CanonicalEntity,
    EntityType,
    RelationType,
    FinancialMetrics,
    MarketTicker
)


# 1. Canonical Company Registries (SEC EDGAR & FIBO aligned)
CANONICAL_COMPANIES: Dict[str, CanonicalEntity] = {
    "NVDA": CanonicalEntity(
        canonical_id="company-nvda",
        entity_type=EntityType.COMPANY,
        name="NVIDIA Corporation",
        ticker="NVDA",
        cik="0001045810",
        sector="Semiconductors & AI Compute",
        country="US",
        market_cap_billions=3150.0,
        aliases=["Nvidia", "NVIDIA Corp", "NVDA", "Nvidia Corporation"]
    ),
    "MSFT": CanonicalEntity(
        canonical_id="company-msft",
        entity_type=EntityType.COMPANY,
        name="Microsoft Corporation",
        ticker="MSFT",
        cik="0000789019",
        sector="Cloud & Enterprise Software",
        country="US",
        market_cap_billions=3100.0,
        aliases=["Microsoft", "Microsoft Corp", "MSFT", "Azure"]
    ),
    "AAPL": CanonicalEntity(
        canonical_id="company-aapl",
        entity_type=EntityType.COMPANY,
        name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
        sector="Consumer Electronics & Ecosystem",
        country="US",
        market_cap_billions=3400.0,
        aliases=["Apple", "Apple Inc", "AAPL", "Apple Computer"]
    ),
    "GOOGL": CanonicalEntity(
        canonical_id="company-googl",
        entity_type=EntityType.COMPANY,
        name="Alphabet Inc.",
        ticker="GOOGL",
        cik="0001652044",
        sector="Internet & Artificial Intelligence",
        country="US",
        market_cap_billions=2100.0,
        aliases=["Google", "Alphabet", "GOOGL", "Alphabet Inc"]
    ),
    "AMZN": CanonicalEntity(
        canonical_id="company-amzn",
        entity_type=EntityType.COMPANY,
        name="Amazon.com, Inc.",
        ticker="AMZN",
        cik="0001018724",
        sector="E-Commerce & Cloud Infrastructure",
        country="US",
        market_cap_billions=1950.0,
        aliases=["Amazon", "Amazon.com", "AMZN", "AWS"]
    ),
    "TSM": CanonicalEntity(
        canonical_id="company-tsm",
        entity_type=EntityType.COMPANY,
        name="Taiwan Semiconductor Manufacturing Company",
        ticker="TSM",
        cik="0001046179",
        sector="Semiconductor Foundry",
        country="TW",
        market_cap_billions=880.0,
        aliases=["TSMC", "Taiwan Semiconductor", "TSM"]
    ),
    "ASML": CanonicalEntity(
        canonical_id="company-asml",
        entity_type=EntityType.COMPANY,
        name="ASML Holding N.V.",
        ticker="ASML",
        cik="0000937966",
        sector="Semiconductor Lithography Equipment",
        country="NL",
        market_cap_billions=380.0,
        aliases=["ASML", "ASML Holding", "ASML N.V."]
    ),
    "AVGO": CanonicalEntity(
        canonical_id="company-avgo",
        entity_type=EntityType.COMPANY,
        name="Broadcom Inc.",
        ticker="AVGO",
        cik="0001730168",
        sector="Semiconductors & Infrastructure Software",
        country="US",
        market_cap_billions=750.0,
        aliases=["Broadcom", "Broadcom Inc", "AVGO"]
    ),
    "TSLA": CanonicalEntity(
        canonical_id="company-tsla",
        entity_type=EntityType.COMPANY,
        name="Tesla, Inc.",
        ticker="TSLA",
        cik="0001318605",
        sector="Automotive & Clean Energy Robotics",
        country="US",
        market_cap_billions=680.0,
        aliases=["Tesla", "Tesla Motors", "TSLA"]
    ),
    "AMD": CanonicalEntity(
        canonical_id="company-amd",
        entity_type=EntityType.COMPANY,
        name="Advanced Micro Devices, Inc.",
        ticker="AMD",
        cik="0000002488",
        sector="Semiconductors & High-Performance Compute",
        country="US",
        market_cap_billions=220.0,
        aliases=["AMD", "Advanced Micro Devices", "Radeon"]
    )
}

# 2. Canonical Executives
CANONICAL_EXECUTIVES: Dict[str, CanonicalEntity] = {
    "jensen-huang": CanonicalEntity(
        canonical_id="exec-jensen-huang",
        entity_type=EntityType.EXECUTIVE,
        name="Jensen Huang",
        aliases=["Jensen Huang", "Jen-Hsun Huang", "CEO Jensen"]
    ),
    "satya-nadella": CanonicalEntity(
        canonical_id="exec-satya-nadella",
        entity_type=EntityType.EXECUTIVE,
        name="Satya Nadella",
        aliases=["Satya Nadella", "Satya", "Chairman Nadella"]
    ),
    "tim-cook": CanonicalEntity(
        canonical_id="exec-tim-cook",
        entity_type=EntityType.EXECUTIVE,
        name="Tim Cook",
        aliases=["Tim Cook", "Timothy D. Cook"]
    ),
    "sundar-pichai": CanonicalEntity(
        canonical_id="exec-sundar-pichai",
        entity_type=EntityType.EXECUTIVE,
        name="Sundar Pichai",
        aliases=["Sundar Pichai", "Pichai"]
    ),
    "andy-jassy": CanonicalEntity(
        canonical_id="exec-andy-jassy",
        entity_type=EntityType.EXECUTIVE,
        name="Andy Jassy",
        aliases=["Andy Jassy", "Andrew Jassy"]
    ),
    "lisa-su": CanonicalEntity(
        canonical_id="exec-lisa-su",
        entity_type=EntityType.EXECUTIVE,
        name="Lisa Su",
        aliases=["Dr. Lisa Su", "Lisa Su"]
    ),
    "elon-musk": CanonicalEntity(
        canonical_id="exec-elon-musk",
        entity_type=EntityType.EXECUTIVE,
        name="Elon Musk",
        aliases=["Elon Musk", "Technoking Elon"]
    )
}

# 3. Canonical Strategic Relationships (Ecosystem Graph)
CANONICAL_RELATIONSHIPS = [
    # ASML upstream lithography monopoly
    {"source": "company-asml", "target": "company-tsm", "relation": RelationType.SUPPLIES_TO, "weight": 0.98, "desc": "Exclusive EUV extreme ultraviolet photolithography equipment"},
    
    # TSMC foundry fabrications
    {"source": "company-tsm", "target": "company-nvda", "relation": RelationType.SUPPLIES_TO, "weight": 0.95, "desc": "Exclusive advanced 4N/3nm wafer fab & CoWoS advanced packaging for Hopper & Blackwell GPUs"},
    {"source": "company-tsm", "target": "company-aapl", "relation": RelationType.SUPPLIES_TO, "weight": 0.92, "desc": "Leading customer for 3nm M-series and A18 Bionic iPhone processors"},
    {"source": "company-tsm", "target": "company-amd", "relation": RelationType.SUPPLIES_TO, "weight": 0.90, "desc": "Advanced packaging for MI300X AI accelerators and EPYC server CPUs"},
    {"source": "company-tsm", "target": "company-avgo", "relation": RelationType.SUPPLIES_TO, "weight": 0.85, "desc": "Custom ASIC semiconductor fabrication"},

    # Nvidia AI infrastructure to Cloud hyperscalers
    {"source": "company-nvda", "target": "company-msft", "relation": RelationType.SUPPLIES_TO, "weight": 0.88, "desc": "Tens of thousands of H100/H200/GB200 clusters powering Azure OpenAI"},
    {"source": "company-nvda", "target": "company-amzn", "relation": RelationType.SUPPLIES_TO, "weight": 0.82, "desc": "DGX Cloud & Hopper GPU instances on AWS EC2"},
    {"source": "company-nvda", "target": "company-googl", "relation": RelationType.SUPPLIES_TO, "weight": 0.78, "desc": "GPU compute alongside Google TPU v5e pods"},
    {"source": "company-nvda", "target": "company-tsla", "relation": RelationType.SUPPLIES_TO, "weight": 0.80, "desc": "50,000+ H100 supercluster powering Tesla Full Self-Driving (FSD) training"},

    # Direct Competitions
    {"source": "company-nvda", "target": "company-amd", "relation": RelationType.COMPETES_WITH, "weight": 0.90, "desc": "Discrete GPUs and Data Center AI Accelerators (Blackwell vs MI325X)"},
    {"source": "company-msft", "target": "company-amzn", "relation": RelationType.COMPETES_WITH, "weight": 0.95, "desc": "Cloud Infrastructure hyperscalers (Azure vs AWS)"},
    {"source": "company-msft", "target": "company-googl", "relation": RelationType.COMPETES_WITH, "weight": 0.92, "desc": "Enterprise Productivity, Cloud & Foundation AI Models (Copilot vs Gemini)"},
    {"source": "company-aapl", "target": "company-googl", "relation": RelationType.COMPETES_WITH, "weight": 0.88, "desc": "Mobile OS & App Ecosystem (iOS vs Android)"},

    # Executive Leadership
    {"source": "exec-jensen-huang", "target": "company-nvda", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "President, Founder and Chief Executive Officer"},
    {"source": "exec-satya-nadella", "target": "company-msft", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "Chairman and Chief Executive Officer"},
    {"source": "exec-tim-cook", "target": "company-aapl", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "Chief Executive Officer"},
    {"source": "exec-sundar-pichai", "target": "company-googl", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "Chief Executive Officer Alphabet & Google"},
    {"source": "exec-andy-jassy", "target": "company-amzn", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "President and Chief Executive Officer"},
    {"source": "exec-lisa-su", "target": "company-amd", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "Chair and Chief Executive Officer"},
    {"source": "exec-elon-musk", "target": "company-tsla", "relation": RelationType.OFFICER_OF, "weight": 1.0, "desc": "Chief Executive Officer & Technoking"}
]

# 4. Comprehensive Financial Statements (for Ratio & Altman Z Analysis)
FINANCIAL_RECORDS: Dict[str, FinancialMetrics] = {
    "NVDA": FinancialMetrics(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        fiscal_year=2024,
        revenue_billions=60.92,
        gross_profit_billions=44.30,
        operating_income_ebit_billions=32.97,
        net_income_billions=29.76,
        total_assets_billions=65.73,
        total_liabilities_billions=22.75,
        current_assets_billions=44.34,
        current_liabilities_billions=10.63,
        retained_earnings_billions=33.62,
        market_cap_billions=3150.0,
        operating_cash_flow_billions=28.09
    ),
    "MSFT": FinancialMetrics(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        fiscal_year=2024,
        revenue_billions=245.12,
        gross_profit_billions=170.72,
        operating_income_ebit_billions=109.43,
        net_income_billions=88.14,
        total_assets_billions=512.16,
        total_liabilities_billions=243.69,
        current_assets_billions=168.95,
        current_liabilities_billions=125.75,
        retained_earnings_billions=118.50,
        market_cap_billions=3100.0,
        operating_cash_flow_billions=118.55
    ),
    "AAPL": FinancialMetrics(
        ticker="AAPL",
        company_name="Apple Inc.",
        fiscal_year=2024,
        revenue_billions=385.60,
        gross_profit_billions=178.10,
        operating_income_ebit_billions=118.40,
        net_income_billions=97.00,
        total_assets_billions=352.58,
        total_liabilities_billions=290.44,
        current_assets_billions=143.57,
        current_liabilities_billions=145.31,
        retained_earnings_billions=-0.21,  # Apple uses share buybacks reducing retained earnings
        market_cap_billions=3400.0,
        operating_cash_flow_billions=110.54
    ),
    "TSM": FinancialMetrics(
        ticker="TSM",
        company_name="Taiwan Semiconductor Manufacturing Company",
        fiscal_year=2024,
        revenue_billions=69.30,
        gross_profit_billions=37.70,
        operating_income_ebit_billions=29.50,
        net_income_billions=26.90,
        total_assets_billions=178.40,
        total_liabilities_billions=71.20,
        current_assets_billions=68.50,
        current_liabilities_billions=31.10,
        retained_earnings_billions=89.20,
        market_cap_billions=880.0,
        operating_cash_flow_billions=39.80
    ),
    "ASML": FinancialMetrics(
        ticker="ASML",
        company_name="ASML Holding N.V.",
        fiscal_year=2024,
        revenue_billions=27.56,
        gross_profit_billions=14.14,
        operating_income_ebit_billions=8.84,
        net_income_billions=7.84,
        total_assets_billions=39.90,
        total_liabilities_billions=25.20,
        current_assets_billions=18.60,
        current_liabilities_billions=15.10,
        retained_earnings_billions=12.40,
        market_cap_billions=380.0,
        operating_cash_flow_billions=5.44
    ),
    "AMZN": FinancialMetrics(
        ticker="AMZN",
        company_name="Amazon.com, Inc.",
        fiscal_year=2024,
        revenue_billions=574.78,
        gross_profit_billions=270.05,
        operating_income_ebit_billions=36.85,
        net_income_billions=30.42,
        total_assets_billions=527.85,
        total_liabilities_billions=326.11,
        current_assets_billions=169.80,
        current_liabilities_billions=175.00,
        retained_earnings_billions=114.30,
        market_cap_billions=1950.0,
        operating_cash_flow_billions=84.95
    )
}

# 5. Live Market Ticker Quotes
MARKET_TICKERS: List[MarketTicker] = [
    MarketTicker(ticker="NVDA", name="NVIDIA Corp", price=128.45, change_dollar=4.20, change_pct=3.38, volume_m=64.2, sector="Semiconductors", updated_at="16:00:00 EST"),
    MarketTicker(ticker="MSFT", name="Microsoft Corp", price=418.12, change_dollar=2.85, change_pct=0.69, volume_m=22.8, sector="Software", updated_at="16:00:00 EST"),
    MarketTicker(ticker="AAPL", name="Apple Inc", price=224.23, change_dollar=-1.15, change_pct=-0.51, volume_m=48.1, sector="Hardware", updated_at="16:00:00 EST"),
    MarketTicker(ticker="TSM", name="TSMC ADR", price=172.90, change_dollar=5.60, change_pct=3.35, volume_m=18.4, sector="Foundry", updated_at="16:00:00 EST"),
    MarketTicker(ticker="ASML", name="ASML Holding", price=798.50, change_dollar=14.30, change_pct=1.82, volume_m=3.1, sector="Lithography", updated_at="16:00:00 EST"),
    MarketTicker(ticker="GOOGL", name="Alphabet Inc", price=168.30, change_dollar=1.40, change_pct=0.84, volume_m=26.5, sector="Internet", updated_at="16:00:00 EST"),
    MarketTicker(ticker="AMZN", name="Amazon.com", price=186.40, change_dollar=3.10, change_pct=1.69, volume_m=34.9, sector="Cloud/Retail", updated_at="16:00:00 EST"),
    MarketTicker(ticker="TSLA", name="Tesla Inc", price=218.80, change_dollar=-3.40, change_pct=-1.53, volume_m=58.3, sector="Automotive", updated_at="16:00:00 EST")
]
