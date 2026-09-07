"""SEC EDGAR XBRL 'company facts' reader — turns https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json into
annual (10-K) series usable by the ratios, comps and merger engines. Public-domain data, no API key; SEC asks for a
descriptive User-Agent with a contact e-mail and ≤10 requests/second.

    facts = fetch(789019, user_agent="my-tool contact@example.com")     # Microsoft
    rows = annual(facts)          # {fy_end: {"revenue": ..., "operating_income": ..., ...}}
    fy = rows["2023-06-30"]

Tag choice follows the same preference order most open-source readers use (FinModeling, AlphaAnalyst): the first
tag present wins; values are taken from the 10-K 'FY' fact whose period ends on the fiscal year end (latest filing wins,
so restated numbers replace originals)."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

TAGS: Dict[str, Sequence[str]] = {
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
    "gross_profit": ("GrossProfit",),
    "operating_income": ("OperatingIncomeLoss",),
    "pretax_income": ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
    "tax": ("IncomeTaxExpenseBenefit",),
    "net_income": ("NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"),
    "da": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet", "Depreciation"),
    "interest_expense": ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt", "InterestAndDebtExpense"),
    "interest_income": ("InvestmentIncomeInterest", "InterestIncomeOther", "InvestmentIncomeInterestAndDividend"),
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsAndShortTermInvestments", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "short_term_investments": ("ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"),
    "debt_current": ("DebtCurrent", "LongTermDebtCurrent", "ShortTermBorrowings", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
    "debt_noncurrent": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndFinanceLeasesNoncurrent"),
    "debt_total": ("LongTermDebt", "DebtLongtermAndShorttermCombinedAmount", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities"),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "nci": ("MinorityInterest",),
    "total_assets": ("Assets",),
    "total_liabilities": ("Liabilities",),
    "current_assets": ("AssetsCurrent",),
    "current_liabilities": ("LiabilitiesCurrent",),
    "receivables": ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"),
    "inventory": ("InventoryNet",),
    "ppe": ("PropertyPlantAndEquipmentNet",),
    "goodwill": ("Goodwill",),
    "intangibles": ("IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"),
    "retained_earnings": ("RetainedEarningsAccumulatedDeficit",),
    "cfo": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
    # NOT a fallback for "capex": some filers (e.g. airlines) split capex into asset-class components that are
    # ADDITIVE, not alternative tags for the same figure — real, verified on Alaska Air Group's own FY2024 10-K,
    # where PaymentsForFlightEquipment ($817M) alone understates real total capex by ~26% against
    # PaymentsForFlightEquipment + PaymentsToAcquireOtherPropertyPlantAndEquipment ($817M + $293M = $1,110M).
    # Summed into "capex" below only when the primary aggregate tag is absent — same pattern as debt_total.
    "capex_flight_equipment": ("PaymentsForFlightEquipment",),
    "capex_other_ppe": ("PaymentsToAcquireOtherPropertyPlantAndEquipment",),
    "dividends": ("PaymentsOfDividends", "PaymentsOfDividendsCommonStock"),
    "diluted_shares": ("WeightedAverageNumberOfDilutedSharesOutstanding",),
    "basic_shares": ("WeightedAverageNumberOfSharesOutstandingBasic",),
    "eps_diluted": ("EarningsPerShareDiluted",),
    "sga": ("SellingGeneralAndAdministrativeExpense",),
    "rnd": ("ResearchAndDevelopmentExpense",),
    "operating_lease_cost": ("OperatingLeaseCost", "OperatingLeaseExpense"),
    # deliberately separate fields, NOT fallbacks for operating_lease_cost: for a filer that doesn't disaggregate
    # (e.g. Southwest), the aggregate "LeaseCost" is dominated by variable lease cost, which ASC 842 expenses as
    # incurred with no matching capitalized liability — folding it into "operating lease cost" would badly
    # overstate an EBITDAR add-back. See finmodel.sectors.SECTOR_PROFILES['airline'].
    "total_lease_cost": ("LeaseCost",),
    "variable_lease_cost": ("VariableLeaseCost",),
    # pre-ASC-842 (fiscal years before ~2019) rent expense — the only lease signal available before operating
    # leases went on the balance sheet; useful for the old rule-of-thumb "capitalize rent at 7-8x" EBITDAR
    # estimate on a filing this old, since operating_lease_cost/_liability won't exist for it at all.
    "pre_842_rent_expense": ("OperatingLeasesRentExpenseNet", "AircraftRental"),
    "operating_lease_liability_current": ("OperatingLeaseLiabilityCurrent",),
    "operating_lease_liability_noncurrent": ("OperatingLeaseLiabilityNoncurrent",),
}
FLOW = {"revenue", "cogs", "gross_profit", "operating_income", "pretax_income", "tax", "net_income", "da", "interest_expense", "interest_income", "cfo", "capex", "dividends", "diluted_shares", "basic_shares", "eps_diluted", "sga", "rnd", "operating_lease_cost", "total_lease_cost", "variable_lease_cost", "pre_842_rent_expense", "capex_flight_equipment", "capex_other_ppe"}


def fetch(cik: int | str, user_agent: str, cache_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Download (or read from cache_dir) the company-facts JSON for a CIK."""
    cik = int(cik)
    if cache_dir:
        p = Path(cache_dir) / f"CIK{cik:010d}.json"
        if p.exists():
            return json.loads(p.read_text())
    req = urllib.request.Request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip; raw = gzip.decompress(raw)
    data = json.loads(raw)
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True); (Path(cache_dir) / f"CIK{cik:010d}.json").write_text(json.dumps(data))
    return data


def _facts(facts: Dict[str, Any], tag: str) -> List[Dict[str, Any]]:
    node = facts.get("facts", {}).get("us-gaap", {}).get(tag)
    if not node: return []
    out = []
    for unit, rows in node.get("units", {}).items():
        for r in rows:
            r = dict(r); r["unit"] = unit; out.append(r)
    return out


def annual(facts: Dict[str, Any], tags: Dict[str, Sequence[str]] = TAGS, forms: Iterable[str] = ("10-K", "10-K/A", "20-F", "40-F")) -> Dict[str, Dict[str, Any]]:
    """Annual values keyed by fiscal-year-end date (ISO). Flow items must span ~a year (330–380 days); balance items are
    instants on the FY end. For each (field, fy_end) the latest-filed fact wins."""
    forms = set(forms); out: Dict[str, Dict[str, Any]] = {}
    from datetime import date
    for field, cands in tags.items():
        picked: Dict[str, tuple] = {}          # end -> (priority, filed, val, tag, unit)
        for prio, tag in enumerate(cands):
            for r in _facts(facts, tag):
                if r.get("form") not in forms or r.get("fp") != "FY": continue
                end = r.get("end"); start = r.get("start")
                if field in FLOW:
                    if not start: continue
                    days = (date.fromisoformat(end) - date.fromisoformat(start)).days
                    if not 330 <= days <= 380: continue
                prev = picked.get(end)
                # a higher-priority tag always wins for that year; within a tag the latest filing wins
                if prev is None or prio < prev[0] or (prio == prev[0] and r.get("filed", "") > prev[1]):
                    picked[end] = (prio, r.get("filed", ""), r["val"], tag, r["unit"])
        for end, (prio, filed, val, tag, unit) in picked.items():
            out.setdefault(end, {"fy_end": end})[field] = val
            out[end].setdefault("_tags", {})[field] = tag
    for end, row in out.items():
        d = row
        if "debt_total" not in d and ("debt_current" in d or "debt_noncurrent" in d):
            d["debt_total"] = d.get("debt_current", 0) + d.get("debt_noncurrent", 0)
        if "capex" not in d and ("capex_flight_equipment" in d or "capex_other_ppe" in d):
            d["capex"] = d.get("capex_flight_equipment", 0) + d.get("capex_other_ppe", 0)
        if "operating_lease_liability_current" in d or "operating_lease_liability_noncurrent" in d:
            # ASC 842 (effective FY2019+) put operating leases on the balance sheet with a real, filed present
            # value — this used to be off-balance-sheet, estimated by capitalizing rent at a rule-of-thumb
            # multiple (e.g. 7-8x annual rent) for lease-heavy sectors like airlines and retail. Post-ASC 842,
            # that estimate is obsolete wherever this real figure is available; see SECTOR_PROFILES['airline'].
            d["operating_lease_liability_total"] = d.get("operating_lease_liability_current", 0) + d.get("operating_lease_liability_noncurrent", 0)
        if "gross_profit" not in d and "revenue" in d and "cogs" in d:
            d["gross_profit"] = d["revenue"] - d["cogs"]
        if "operating_income" not in d and "pretax_income" in d:
            d["operating_income"] = d["pretax_income"] + d.get("interest_expense", 0) - d.get("interest_income", 0); d.setdefault("_tags", {})["operating_income"] = "derived: pretax + interest expense − interest income"
        if "operating_income" in d and "da" in d:
            d["ebitda"] = d["operating_income"] + d["da"]
        if not d.get("diluted_shares") and d.get("net_income") and d.get("eps_diluted"):
            # some filers (e.g. Exxon Mobil in recent 10-Ks) report basic shares plus diluted EPS but no
            # WeightedAverageNumberOfDilutedSharesOutstanding tag; back it out from EPS = NI / diluted shares.
            # A small approximation when NCI or preferred dividends separate NI from the EPS numerator.
            d["diluted_shares"] = d["net_income"] / d["eps_diluted"]; d.setdefault("_tags", {})["diluted_shares"] = "derived: net_income / eps_diluted"
        if "cash" in d:
            d["net_debt"] = d.get("debt_total", 0) - d["cash"] - d.get("short_term_investments", 0)
    return dict(sorted(out.items()))


def compact(facts: Dict[str, Any], years: int = 12) -> Dict[str, Any]:
    """Small JSON-able extract (entity + last `years` fiscal years) for committing alongside a case study."""
    rows = annual(facts)
    keep = list(rows)[-years:]
    return {"cik": facts.get("cik"), "entity": facts.get("entityName"), "years": {k: {kk: v for kk, v in rows[k].items() if kk != "_tags"} for k in keep}, "tags": {k: rows[k]["_tags"] for k in keep[-1:]}}


def to_ratio_inputs(row: Dict[str, Any]) -> tuple:
    """Map an annual row onto the (income statement, balance sheet) dicts that finmodel.ratios.compute expects."""
    is_ = {"revenue": row.get("revenue", 0), "cogs": row.get("cogs", row.get("revenue", 0) - row.get("gross_profit", 0)), "gross_profit": row.get("gross_profit", 0),
           "ebit": row.get("operating_income", 0), "ebitda": row.get("ebitda", row.get("operating_income", 0)), "da": row.get("da", 0),
           "interest_expense": row.get("interest_expense", 0), "pretax_income": row.get("pretax_income", 0), "tax": row.get("tax", 0), "net_income": row.get("net_income", 0),
           "diluted_shares": row.get("diluted_shares", 0), "eps": row.get("eps_diluted", 0), "cfo": row.get("cfo", 0), "capex": row.get("capex", 0), "dividends": row.get("dividends", 0)}
    bs = {"cash": row.get("cash", 0), "receivables": row.get("receivables", 0), "inventory": row.get("inventory", 0), "current_assets": row.get("current_assets", 0),
          "ppe": row.get("ppe", 0), "goodwill": row.get("goodwill", 0), "intangibles": row.get("intangibles", 0), "total_assets": row.get("total_assets", 0),
          "current_liabilities": row.get("current_liabilities", 0), "debt": row.get("debt_total", 0), "total_liabilities": row.get("total_liabilities", 0),
          "equity": row.get("equity", 0), "retained_earnings": row.get("retained_earnings", 0), "nci": row.get("nci", 0)}
    return is_, bs
