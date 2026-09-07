import json
from pathlib import Path
import pytest
from finmodel import edgar


def fact(tag, val, end, start=None, form="10-K", fp="FY", filed="2024-02-01", unit="USD"):
    r = {"val": val, "end": end, "form": form, "fp": fp, "filed": filed, "accn": "x", "fy": int(end[:4])}
    if start: r["start"] = start
    return tag, unit, r


def facts(*items):
    gaap = {}
    for tag, unit, r in items:
        gaap.setdefault(tag, {"units": {}})["units"].setdefault(unit, []).append(r)
    return {"cik": 1, "entityName": "TestCo", "facts": {"us-gaap": gaap}}


def test_annual_tag_precedence_and_restatement():
    f = facts(fact("Revenues", 100, "2022-12-31", "2022-01-01"),                                   # older tag, FY2022
              fact("RevenueFromContractWithCustomerExcludingAssessedTax", 200, "2023-12-31", "2023-01-01"),   # newer tag, FY2023
              fact("RevenueFromContractWithCustomerExcludingAssessedTax", 150, "2022-12-31", "2022-01-01"),   # lower priority for FY2022 → ignored
              fact("NetIncomeLoss", 10, "2023-12-31", "2023-01-01", filed="2024-02-01"),
              fact("NetIncomeLoss", 11, "2023-12-31", "2023-01-01", filed="2025-02-01"),          # restated in the next 10-K → wins
              fact("NetIncomeLoss", 5, "2023-12-31", "2023-10-01", fp="Q4"),                        # quarterly → ignored
              fact("CashAndCashEquivalentsAtCarryingValue", 30, "2023-12-31"),
              fact("LongTermDebtNoncurrent", 40, "2023-12-31"), fact("DebtCurrent", 5, "2023-12-31"),
              fact("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", 12, "2023-12-31", "2023-01-01"),
              fact("InterestExpense", 2, "2023-12-31", "2023-01-01"), fact("DepreciationDepletionAndAmortization", 3, "2023-12-31", "2023-01-01"),
              fact("WeightedAverageNumberOfDilutedSharesOutstanding", 4, "2023-12-31", "2023-01-01", unit="shares"))
    rows = edgar.annual(f)
    assert rows["2022-12-31"]["revenue"] == 100 and rows["2023-12-31"]["revenue"] == 200
    assert rows["2023-12-31"]["net_income"] == 11
    assert rows["2023-12-31"]["debt_total"] == 45 and rows["2023-12-31"]["net_debt"] == 15
    assert rows["2023-12-31"]["operating_income"] == 14 and rows["2023-12-31"]["ebitda"] == 17   # derived from pretax + interest
    c = edgar.compact(f, years=1)
    assert list(c["years"]) == ["2023-12-31"] and "_tags" not in c["years"]["2023-12-31"]
    is_, bs = edgar.to_ratio_inputs(rows["2023-12-31"])
    assert is_["net_income"] == 11 and bs["debt"] == 45


def test_diluted_shares_falls_back_to_net_income_over_eps():
    # Exxon Mobil's recent 10-Ks report basic shares and diluted EPS but no explicit diluted-share-count tag.
    f = facts(fact("Revenues", 1000, "2025-12-31", "2025-01-01"), fact("NetIncomeLoss", 100, "2025-12-31", "2025-01-01"),
              fact("EarningsPerShareDiluted", 2.5, "2025-12-31", "2025-01-01", unit="USD/shares"),
              fact("WeightedAverageNumberOfSharesOutstandingBasic", 39, "2025-12-31", "2025-01-01", unit="shares"))
    rows = edgar.annual(f)
    assert rows["2025-12-31"]["diluted_shares"] == pytest.approx(40.0)   # 100 / 2.5, not the 39 basic count
    assert rows["2025-12-31"]["_tags"]["diluted_shares"].startswith("derived")
    # a filer that DOES report diluted shares directly keeps the reported value, not the derived one
    f2 = facts(fact("Revenues", 1000, "2025-12-31", "2025-01-01"), fact("NetIncomeLoss", 100, "2025-12-31", "2025-01-01"),
               fact("EarningsPerShareDiluted", 2.5, "2025-12-31", "2025-01-01", unit="USD/shares"),
               fact("WeightedAverageNumberOfDilutedSharesOutstanding", 41, "2025-12-31", "2025-01-01", unit="shares"))
    assert edgar.annual(f2)["2025-12-31"]["diluted_shares"] == 41


def test_revenue_falls_back_to_regulated_operating_revenue_tag():
    # Xcel Energy's own consolidated top line moved onto this utility-industry-specific tag starting FY2022 (its
    # plain "Revenues" tag has zero entries from FY2022 onward, real, verified against SEC's live XBRL API) —
    # confirm it's a real fallback, and that a filer with BOTH tags still prefers the more common "Revenues" one.
    f = facts(fact("RegulatedAndUnregulatedOperatingRevenue", 14669, "2025-12-31", "2025-01-01"),
              fact("NetIncomeLoss", 100, "2025-12-31", "2025-01-01"))
    assert edgar.annual(f)["2025-12-31"]["revenue"] == 14669
    f2 = facts(fact("Revenues", 5000, "2025-12-31", "2025-01-01"),
               fact("RegulatedAndUnregulatedOperatingRevenue", 14669, "2025-12-31", "2025-01-01"))
    assert edgar.annual(f2)["2025-12-31"]["revenue"] == 5000


def test_committed_extracts_are_consistent():
    root = Path(__file__).resolve().parent.parent / "data" / "edgar"
    for t in ("MSFT", "STLD", "HES", "DUK", "XEL"):
        d = json.loads((root / f"{t}.json").read_text())
        last = d["years"][sorted(d["years"])[-1]]
        assert last["revenue"] > 0 and last["diluted_shares"] > 0 and abs(last["net_income"] / last["diluted_shares"] - last["eps_diluted"]) / abs(last["eps_diluted"]) < 0.05
