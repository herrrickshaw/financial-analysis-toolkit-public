"""finmodel.vc_fund_metrics: DPI/RVPI/TVPI reconcile to a hand-computed example and their defining identity
(TVPI = DPI + RVPI); IRR is checked against a closed-form two-cashflow case; the carry waterfall is checked for
value conservation and its defining correctness property -- once the GP catch-up fully completes, the GP's
total take is EXACTLY `carry_pct` of total profit above return of capital, not just of the residual split."""
import pytest

from finmodel import vc_fund_metrics as VC


def test_fund_metrics_dpi_rvpi_tvpi_hand_computed():
    cashflows = [VC.CashFlow("2020-01-01", -10_000_000)]
    m = VC.fund_metrics(cashflows, nav=8_000_000, as_of="2024-01-01")
    assert m["paid_in"] == 10_000_000
    assert m["distributions"] == 0
    assert m["dpi"] == pytest.approx(0.0)
    assert m["rvpi"] == pytest.approx(0.8)
    assert m["tvpi"] == pytest.approx(0.8)
    assert m["tvpi"] == pytest.approx(m["dpi"] + m["rvpi"])


def test_fund_metrics_with_partial_distributions():
    cashflows = [VC.CashFlow("2020-01-01", -10_000_000), VC.CashFlow("2023-01-01", 5_000_000)]
    m = VC.fund_metrics(cashflows, nav=8_000_000, as_of="2024-01-01")
    assert m["dpi"] == pytest.approx(0.5)
    assert m["rvpi"] == pytest.approx(0.8)
    assert m["tvpi"] == pytest.approx(1.3)


def test_deal_metrics_irr_matches_closed_form_two_cashflow_case():
    # $10M in, doubling to a $20M current value exactly 2 years later -> IRR = sqrt(2) - 1
    d = VC.deal_metrics(invested=10_000_000, proceeds_to_date=0, current_value=20_000_000,
                        cashflow_dates=["2022-01-01"], cashflow_amounts=[-10_000_000], as_of="2024-01-01")
    assert d["irr"] == pytest.approx(2 ** 0.5 - 1, abs=1e-3)


def test_deal_metrics_moic_is_always_computable_without_dates():
    d = VC.deal_metrics(invested=1_000_000, proceeds_to_date=500_000, current_value=2_000_000)
    assert d["moic"] == pytest.approx(2.5)
    assert "irr" not in d


def test_carry_waterfall_conserves_total_value():
    cashflows = [VC.CashFlow("2019-01-01", -10_000_000)]
    w = VC.carry_waterfall(cashflows, nav=30_000_000, as_of="2024-01-01", hurdle_rate=0.08, carry_pct=0.20)
    assert w["lp_total"] + w["gp_total"] == pytest.approx(w["total_value"])


def test_carry_waterfall_no_profit_means_lps_get_everything():
    cashflows = [VC.CashFlow("2019-01-01", -10_000_000)]
    w = VC.carry_waterfall(cashflows, nav=8_000_000, as_of="2024-01-01", hurdle_rate=0.08, carry_pct=0.20)
    assert w["gp_total"] == pytest.approx(0.0)
    assert w["lp_total"] == pytest.approx(8_000_000)


def test_carry_waterfall_gp_catchup_gives_exactly_target_carry_on_profit():
    # hand-computed (see the module's derivation): $10M paid in, 5-year hold, 8% hurdle, 20% carry, $30M total
    # value -> GP's total take should be EXACTLY 20% of the $20M profit above return-of-capital, once the
    # catch-up tier fully completes (there's enough value left after the hurdle to complete it).
    cashflows = [VC.CashFlow("2019-01-01", -10_000_000)]
    w = VC.carry_waterfall(cashflows, nav=30_000_000, as_of="2024-01-01", hurdle_rate=0.08, carry_pct=0.20)
    assert w["gp_total"] == pytest.approx(4_000_000, rel=1e-6)
    assert w["lp_total"] == pytest.approx(26_000_000, rel=1e-6)
    assert w["effective_carry_pct_of_profit"] == pytest.approx(0.20, abs=1e-9)


def test_carry_waterfall_small_profit_below_catchup_gives_gp_less_than_full_carry():
    # if there isn't enough profit to complete the GP catch-up, the GP's effective carry stays below carry_pct
    # (the LPs' preferred return is protected even when the fund barely clears its hurdle).
    cashflows = [VC.CashFlow("2019-01-01", -10_000_000)]
    w = VC.carry_waterfall(cashflows, nav=15_000_000, as_of="2024-01-01", hurdle_rate=0.08, carry_pct=0.20)
    assert w["effective_carry_pct_of_profit"] < 0.20


def test_from_dict_end_to_end():
    out = VC.from_dict({
        "cashflows": [{"date": "2019-01-01", "amount": -10_000_000}, {"date": "2023-01-01", "amount": 5_000_000}],
        "nav": 8_000_000, "as_of": "2024-01-01",
        "carry": {"hurdle_rate": 0.08, "carry_pct": 0.20},
        "deals": {"Deal 1": {"invested": 1_000_000, "proceeds_to_date": 500_000, "current_value": 2_000_000}},
    })
    assert out["fund_metrics"]["tvpi"] == pytest.approx(1.3)
    assert out["deals"]["Deal 1"]["moic"] == pytest.approx(2.5)
    assert out["carry_waterfall"]["lp_total"] + out["carry_waterfall"]["gp_total"] == pytest.approx(out["carry_waterfall"]["total_value"])


def test_american_waterfall_winner_then_loser_triggers_a_clawback():
    # hand-computed: Deal A (a 3x winner, $1M -> $3M over 1yr) is realized first and pays the GP $400,000 in
    # carry (exactly 20% of the fund's $2M cumulative profit at that point -- see the module's own worked
    # derivation). Deal B (a straight loss, $1M -> $200,000) is realized second, shrinking the fund's
    # cumulative profit to $1.2M -- only $240,000 of carry is now justified, so the GP owes back $160,000.
    deals = [
        {"name": "A", "invested": 1_000_000.0, "proceeds": 3_000_000.0, "invested_date": "2020-01-01", "realized_date": "2021-01-01"},
        {"name": "B", "invested": 1_000_000.0, "proceeds": 200_000.0, "invested_date": "2020-01-01", "realized_date": "2022-01-01"},
    ]
    out = VC.american_waterfall(deals, hurdle_rate=0.08, carry_pct=0.20)
    deal_a, deal_b = out["deals"]
    assert deal_a["gp_payout"] == pytest.approx(400_000.0, rel=1e-4)
    assert deal_a["clawback_owed"] == pytest.approx(0.0, abs=1.0)
    assert deal_b["gp_payout"] == pytest.approx(0.0)  # a straight loss returns none of its own capital, let alone carry
    assert deal_b["cumulative_fund_profit"] == pytest.approx(1_200_000.0)
    assert deal_b["target_cumulative_gp_carry"] == pytest.approx(240_000.0)
    assert deal_b["clawback_owed"] == pytest.approx(160_000.0, rel=1e-3)
    assert out["final_clawback_owed"] == pytest.approx(160_000.0, rel=1e-3)


def test_american_waterfall_two_winners_never_triggers_a_clawback():
    deals = [
        {"name": "A", "invested": 1_000_000.0, "proceeds": 2_000_000.0, "invested_date": "2020-01-01", "realized_date": "2021-01-01"},
        {"name": "B", "invested": 1_000_000.0, "proceeds": 2_500_000.0, "invested_date": "2020-01-01", "realized_date": "2022-01-01"},
    ]
    out = VC.american_waterfall(deals, hurdle_rate=0.08, carry_pct=0.20)
    assert out["final_clawback_owed"] == pytest.approx(0.0, abs=1.0)
    assert all(d["clawback_owed"] == pytest.approx(0.0, abs=1.0) for d in out["deals"])


def test_american_waterfall_processes_deals_in_realization_date_order_regardless_of_input_order():
    deals_in_order = [
        {"name": "A", "invested": 1_000_000.0, "proceeds": 3_000_000.0, "invested_date": "2020-01-01", "realized_date": "2021-01-01"},
        {"name": "B", "invested": 1_000_000.0, "proceeds": 200_000.0, "invested_date": "2020-01-01", "realized_date": "2022-01-01"},
    ]
    reversed_input = list(reversed(deals_in_order))
    out1 = VC.american_waterfall(deals_in_order)
    out2 = VC.american_waterfall(reversed_input)
    assert [d["name"] for d in out1["deals"]] == [d["name"] for d in out2["deals"]] == ["A", "B"]
    assert out1["final_clawback_owed"] == pytest.approx(out2["final_clawback_owed"])


def test_from_dict_includes_american_waterfall():
    out = VC.from_dict({
        "cashflows": [{"date": "2019-01-01", "amount": -1_000_000}], "nav": 0.0, "as_of": "2024-01-01",
        "american_waterfall": {"deals": [
            {"name": "A", "invested": 1_000_000.0, "proceeds": 3_000_000.0, "invested_date": "2020-01-01", "realized_date": "2021-01-01"},
        ]},
    })
    assert out["american_waterfall"]["total_gp_payout"] > 0
