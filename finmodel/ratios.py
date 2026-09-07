"""Financial ratio analysis, distilled from CFI 'Financial Ratio Analysis' sheet
(profitability, efficiency, liquidity, leverage, coverage) plus common returns ratios."""
from __future__ import annotations

from typing import Dict, Any

from .fin import safe_div

REQUIRED_IS = ("revenue", "cogs", "gross_profit", "ebit", "interest", "ebt", "taxes", "net_income")
REQUIRED_BS = ("total_assets", "current_assets", "current_liabilities", "inventory", "ar", "ap",
               "ppe", "long_term_debt", "total_liabilities", "equity")


def compute(is_: Dict[str, float], bs: Dict[str, float], days: int = 365, intangibles: float = 0.0) -> Dict[str, Any]:
    """is_ keys: see REQUIRED_IS ; bs keys: see REQUIRED_BS (missing keys default to 0)."""
    I = {k: float(is_.get(k, 0.0)) for k in REQUIRED_IS}
    B = {k: float(bs.get(k, 0.0)) for k in REQUIRED_BS}
    inv_days = safe_div(B["inventory"] * days, I["cogs"])
    rec_days = safe_div(B["ar"] * days, I["revenue"])
    pay_days = safe_div(B["ap"] * days, I["cogs"])
    return {
        "profitability": {
            "gross_margin": safe_div(I["gross_profit"], I["revenue"]),
            "operating_margin": safe_div(I["ebit"], I["revenue"]),
            "net_profit_margin": safe_div(I["net_income"], I["revenue"]),
            "return_on_assets": safe_div(I["net_income"], B["total_assets"]),
            "return_on_equity": safe_div(I["net_income"], B["equity"]),
        },
        "efficiency": {
            "total_asset_turnover": safe_div(I["revenue"], B["total_assets"]),
            "net_asset_turnover": safe_div(I["revenue"], B["total_assets"] - B["current_liabilities"]),
            "inventory_turnover": safe_div(I["cogs"], B["inventory"]),
            "inventory_days": inv_days,
            "receivable_turnover": safe_div(I["revenue"], B["ar"]),
            "receivable_days": rec_days,
            "payables_turnover": safe_div(I["cogs"], B["ap"]),
            "payables_days": pay_days,
            "working_capital_requirement_days": inv_days + rec_days,
            "working_capital_funding_gap_days": inv_days + rec_days - pay_days,
            "ppe_turnover": safe_div(I["revenue"], B["ppe"]),
            "tax_ratio": safe_div(I["taxes"], I["ebt"]),
        },
        "liquidity": {
            "current_ratio": safe_div(B["current_assets"], B["current_liabilities"]),
            "quick_ratio": safe_div(B["current_assets"] - B["inventory"], B["current_liabilities"]),
        },
        "leverage": {
            "debt_to_equity": safe_div(B["long_term_debt"], B["equity"]),
            "debt_to_tangible_net_worth": safe_div(B["long_term_debt"], B["total_assets"] - B["total_liabilities"] - intangibles),
            "total_liabilities_to_equity": safe_div(B["total_liabilities"], B["equity"]),
            "total_assets_to_equity": safe_div(B["total_assets"], B["equity"]),
        },
        "coverage": {
            "interest_coverage": safe_div(I["ebit"], I["interest"]),
        },
    }


def flatten(r: Dict[str, Any]) -> Dict[str, float]:
    return {f"{sec}.{k}": v for sec, d in r.items() for k, v in d.items()}
