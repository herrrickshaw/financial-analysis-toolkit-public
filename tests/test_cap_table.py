"""finmodel.cap_table: the option-pool-shuffle formula is verified against its own defining invariant (the new
investor's actual post-money ownership must equal investment/post_money exactly, regardless of the pool target
— that's the whole point of doing the pool math pre-money), and the exit waterfall is hand-verified at, below,
and above a non-participating preferred holder's real conversion crossover point."""
import pytest

from finmodel import cap_table as CT


def test_option_pool_shuffle_never_dilutes_the_new_investor():
    # the defining correctness property: whatever the pool target, the new investor's actual post-money
    # ownership must land exactly on investment / (pre_money + investment) -- the pool dilutes existing
    # holders only, never the incoming investor. Checked across a range of pool targets.
    founders = [CT.Holder("Founders", 8_000_000)]
    for target in (0.0, 0.10, 0.15, 0.20):
        rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=target or None,
                           investor_name="Series A investor")]
        result = CT.simulate_rounds(founders, rounds)
        audit = result.rounds_applied[0]
        assert audit["new_investor_ownership_pct"] == pytest.approx(2_000_000 / 10_000_000, abs=1e-9)
        assert audit["new_investor_ownership_pct"] == pytest.approx(audit["new_investor_ownership_pct_intended"])


def test_option_pool_shuffle_hits_the_exact_target_percentage():
    founders = [CT.Holder("Founders", 8_000_000)]
    rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=0.10, investor_name="Series A investor")]
    result = CT.simulate_rounds(founders, rounds)
    pool_shares = next(h.shares for h in result.holders if h.security == "option_pool")
    total = sum(h.shares for h in result.holders)
    assert pool_shares / total == pytest.approx(0.10, abs=1e-9)
    # hand-computed exact values for this example (see tests/test_cap_table.py's module docstring derivation)
    audit = result.rounds_applied[0]
    assert audit["price_per_share"] == pytest.approx(0.875)
    assert audit["option_pool_topup"] == pytest.approx(1_142_857.142857, rel=1e-6)
    assert audit["new_investor_shares"] == pytest.approx(2_285_714.285714, rel=1e-6)


def test_option_pool_shuffle_accounts_for_an_existing_pool():
    founders = [CT.Holder("Founders", 7_000_000), CT.Holder("Option pool", 1_000_000, security="option_pool")]
    rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=0.10, investor_name="Series A investor")]
    result = CT.simulate_rounds(founders, rounds)
    pool_shares = sum(h.shares for h in result.holders if h.security == "option_pool")
    total = sum(h.shares for h in result.holders)
    assert pool_shares / total == pytest.approx(0.10, abs=1e-9)


def test_option_pool_target_infeasible_raises():
    founders = [CT.Holder("Founders", 8_000_000)]
    rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=0.90, investor_name="X")]
    with pytest.raises(ValueError, match="infeasible"):
        CT.simulate_rounds(founders, rounds)


def _series_a_cap_table():
    founders = [CT.Holder("Founders", 8_000_000)]
    rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=0.10,
                       investor_name="Series A investor", liquidation_preference_multiple=1.0, participating=False, seniority=1)]
    return CT.simulate_rounds(founders, rounds)


def test_exit_waterfall_below_crossover_non_participating_takes_the_preference():
    # exit=$3M: Series A's as-converted (20% x $3M = $600K) is below its $2M 1x preference, so it takes the
    # preference; the remaining $1M splits pro-rata between founders (87.5%) and the option pool (12.5%).
    result = _series_a_cap_table()
    w = CT.exit_waterfall(result, exit_proceeds=3_000_000)
    assert w["payouts"]["Series A investor"] == pytest.approx(2_000_000)
    assert w["payouts"]["Founders"] == pytest.approx(875_000)
    assert w["payouts"]["Option pool"] == pytest.approx(125_000)
    assert "Series A investor" not in w["converted_to_common"]
    assert sum(w["payouts"].values()) == pytest.approx(3_000_000)


def test_exit_waterfall_above_crossover_non_participating_converts():
    # exit=$50M: Series A's as-converted (20% x $50M = $10M) exceeds its $2M preference, so it converts and
    # shares pro-rata with everyone else instead -- getting exactly its 20% ownership share of the full proceeds.
    result = _series_a_cap_table()
    w = CT.exit_waterfall(result, exit_proceeds=50_000_000)
    assert "Series A investor" in w["converted_to_common"]
    assert w["payouts"]["Series A investor"] == pytest.approx(10_000_000)
    assert sum(w["payouts"].values()) == pytest.approx(50_000_000)


def test_exit_waterfall_at_the_exact_crossover_ties_go_to_the_preference():
    # exit=$10M is the exact point where as-converted ($10M x 20% = $2M) equals the $2M preference -- the
    # module's tie-breaking convention (strict > required to convert) means it takes the preference here.
    result = _series_a_cap_table()
    w = CT.exit_waterfall(result, exit_proceeds=10_000_000)
    assert "Series A investor" not in w["converted_to_common"]
    assert w["payouts"]["Series A investor"] == pytest.approx(2_000_000)


def test_exit_waterfall_participating_preferred_double_dips():
    # same cap table, but Series A is participating: it takes its $2M preference off the top AND THEN also
    # shares pro-rata in the $8M remainder alongside common and the option pool (the real "double dip").
    founders = [CT.Holder("Founders", 8_000_000)]
    rounds = [CT.Round("Series A", pre_money=8_000_000, investment=2_000_000, target_option_pool_pct=0.10,
                       investor_name="Series A investor", liquidation_preference_multiple=1.0, participating=True, seniority=1)]
    result = CT.simulate_rounds(founders, rounds)
    w = CT.exit_waterfall(result, exit_proceeds=10_000_000)
    assert w["payouts"]["Series A investor"] == pytest.approx(2_000_000 + 1_600_000)  # preference + 20% of the $8M remainder
    assert w["payouts"]["Founders"] == pytest.approx(5_600_000)
    assert w["payouts"]["Option pool"] == pytest.approx(800_000)
    assert sum(w["payouts"].values()) == pytest.approx(10_000_000)


def test_from_dict_end_to_end():
    out = CT.from_dict({
        "initial_holders": [{"name": "Founders", "shares": 8_000_000}],
        "rounds": [{"name": "Series A", "pre_money": 8_000_000, "investment": 2_000_000,
                    "target_option_pool_pct": 0.10, "investor_name": "Series A investor"}],
        "exit_proceeds": 20_000_000,
    })
    assert out["cap_table"]["ownership"]["Founders"] == pytest.approx(0.7)
    assert sum(out["exit_waterfall"]["payouts"].values()) == pytest.approx(20_000_000)
