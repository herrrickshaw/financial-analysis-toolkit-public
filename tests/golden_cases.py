"""Golden-case builders: run the valuation engines on tracked example inputs and return JSON-able results.

`tests/golden/*.json` were captured from the pre-refactor code; test_golden.py asserts the engines still reproduce
them exactly. Regenerate only for an intentional numeric change: `python tests/golden_cases.py --write`."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
GOLDEN = Path(__file__).resolve().parent / "golden"


def _ex(name: str) -> dict:
    return json.loads((ROOT / "examples" / name).read_text())


def edgar_facts() -> dict:
    """Synthetic company-facts payload (no network) exercising tag precedence, restatement, derived fields."""
    def f(tag, val, end, start=None, form="10-K", fp="FY", filed="2024-02-01", unit="USD"):
        r = {"val": val, "end": end, "form": form, "fp": fp, "filed": filed, "accn": "x", "fy": int(end[:4])}
        if start:
            r["start"] = start
        return tag, unit, r
    items = [f("Revenues", 100, "2022-12-31", "2022-01-01"),
             f("RevenueFromContractWithCustomerExcludingAssessedTax", 200, "2023-12-31", "2023-01-01"),
             f("RevenueFromContractWithCustomerExcludingAssessedTax", 150, "2022-12-31", "2022-01-01"),
             f("NetIncomeLoss", 10, "2023-12-31", "2023-01-01"), f("NetIncomeLoss", 11, "2023-12-31", "2023-01-01", filed="2025-02-01"),
             f("NetIncomeLoss", 5, "2023-12-31", "2023-10-01", fp="Q4"),
             f("CashAndCashEquivalentsAtCarryingValue", 30, "2023-12-31"),
             f("ShortTermInvestments", 4, "2023-12-31"),
             f("LongTermDebtNoncurrent", 40, "2023-12-31"), f("DebtCurrent", 5, "2023-12-31"),
             f("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", 12, "2023-12-31", "2023-01-01"),
             f("InterestExpense", 2, "2023-12-31", "2023-01-01"), f("InvestmentIncomeInterest", 1, "2023-12-31", "2023-01-01"),
             f("Depreciation", 3, "2023-12-31", "2023-01-01"), f("AmortizationOfIntangibleAssets", 7, "2023-12-31", "2023-01-01"),
             f("PaymentsForFlightEquipment", 8, "2023-12-31", "2023-01-01"), f("PaymentsToAcquireOtherPropertyPlantAndEquipment", 2, "2023-12-31", "2023-01-01"),
             f("OperatingLeaseLiabilityCurrent", 6, "2023-12-31"), f("OperatingLeaseLiabilityNoncurrent", 9, "2023-12-31"),
             f("CostOfRevenue", 120, "2023-12-31", "2023-01-01"),
             f("EarningsPerShareDiluted", 2.5, "2023-12-31", "2023-01-01", unit="USD/shares")]
    gaap = {}
    for tag, unit, r in items:
        gaap.setdefault(tag, {"units": {}})["units"].setdefault(unit, []).append(r)
    return {"cik": 1, "entityName": "TestCo", "facts": {"us-gaap": gaap}}


def build() -> dict:
    from finmodel import comps, dcf, edgar, lbo, merger
    d = _ex("cfi_dcf.json")
    inp = dcf.DCFInputs(**dcf.clean(d))
    rows = edgar.annual(edgar_facts())
    return {
        "comps_stld": comps.from_dict(_ex("comps_stld.json")),
        "dcf_cfi": dcf.from_dict(d),
        "dcf_mid_year": dcf.run(replace(inp, mid_year=True, terminal_method="perpetuity")),
        "dcf_sensitivity": dcf.sensitivity(inp, [0.10, 0.12, 0.14], [0.02, 0.03, 0.04]),
        "lbo_asm": lbo.from_dict(_ex("lbo_asm.json")),
        "merger_biws": merger.from_dict(_ex("merger_biws.json")),
        "edgar_annual": rows,
        "edgar_compact": edgar.compact(edgar_facts(), years=2),
        "edgar_ratio_inputs": edgar.to_ratio_inputs(rows["2023-12-31"]),
    }


def dump(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, default=str)


if __name__ == "__main__":
    if "--write" in sys.argv:
        GOLDEN.mkdir(exist_ok=True)
        for k, v in build().items():
            (GOLDEN / f"{k}.json").write_text(dump(v) + "\n")
        print("wrote", GOLDEN)
