import json
from pathlib import Path
import pytest
from finmodel import ratios


def test_ratios_match_cfi_definitions():
    d = json.loads((Path(__file__).resolve().parent.parent / "examples" / "ratios_demo.json").read_text())
    r = ratios.compute(d["is"], d["bs"])
    assert r["profitability"]["gross_margin"] == pytest.approx(94062 / 150772)
    assert r["efficiency"]["inventory_days"] == pytest.approx(11342 * 365 / 56710)
    assert r["efficiency"]["working_capital_funding_gap_days"] == pytest.approx(11342 * 365 / 56710 + 7538 * 365 / 150772 - 5670 * 365 / 56710)
    assert r["liquidity"]["quick_ratio"] == pytest.approx((158429 - 11342) / 5670)
    assert r["leverage"]["debt_to_tangible_net_worth"] == pytest.approx(30000 / (195950 - 35670))
    assert r["coverage"]["interest_coverage"] == pytest.approx(41325 / 1500)
    assert ratios.compute({}, {})["liquidity"]["current_ratio"] == 0.0  # IFERROR -> 0
    assert "efficiency.ppe_turnover" in ratios.flatten(r)
