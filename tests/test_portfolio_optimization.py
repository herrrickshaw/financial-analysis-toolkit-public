"""finmodel.portfolio_optimization: the Gauss-Jordan inverse is checked against a hand-invertible 2x2 case, the
efficient frontier's closed form is checked for its defining internal-consistency property (the frontier point at
target return R = B/A must exactly equal the independently-computed global minimum-variance portfolio), and the
tangency portfolio is checked for the real property that gives it its name (maximum Sharpe ratio among all
frontier portfolios)."""
import pytest

from finmodel import portfolio_optimization as PO

MU = [0.08, 0.12, 0.15]
COV = [[0.04, 0.01, 0.02], [0.01, 0.09, 0.03], [0.02, 0.03, 0.16]]


def test_invert_2x2_matches_hand_calc():
    m = [[4.0, 7.0], [2.0, 6.0]]
    inv = PO._invert(m)
    # det = 4*6-7*2=10; inverse = 1/det * [[6,-7],[-2,4]]
    assert inv[0] == pytest.approx([0.6, -0.7])
    assert inv[1] == pytest.approx([-0.2, 0.4])


def test_invert_raises_on_singular_matrix():
    with pytest.raises(ValueError):
        PO._invert([[1.0, 2.0], [2.0, 4.0]])


def test_global_minimum_variance_weights_sum_to_one():
    out = PO.global_minimum_variance_portfolio(COV)
    assert sum(out["weights"]) == pytest.approx(1.0)


def test_efficient_frontier_at_gmv_return_matches_gmv_portfolio_exactly():
    # the real, defining internal-consistency check: the frontier's closed form, evaluated at R = B/A (the GMV's
    # own expected return), must reproduce the independently-computed GMV weights and variance exactly.
    gmv = PO.global_minimum_variance_portfolio(COV)
    inv = PO._invert(COV)
    ones = [1.0] * 3
    A = PO._dot(ones, PO._matvec(inv, ones))
    B = PO._dot(ones, PO._matvec(inv, MU))
    target = B / A
    frontier_point = PO.efficient_frontier(MU, COV, [target])[0]
    assert frontier_point["weights"] == pytest.approx(gmv["weights"])
    assert frontier_point["variance"] == pytest.approx(gmv["variance"])


def test_efficient_frontier_weights_always_sum_to_one():
    for point in PO.efficient_frontier(MU, COV, [0.08, 0.10, 0.12, 0.14]):
        assert sum(point["weights"]) == pytest.approx(1.0)


def test_tangency_portfolio_has_higher_sharpe_than_gmv():
    # the real property that gives the tangency portfolio its name: it maximizes Sharpe ratio among ALL
    # portfolios of risky assets, so it must beat the (unconstrained-by-return) global minimum-variance one.
    gmv = PO.global_minimum_variance_portfolio(COV)
    gmv_stats = PO.portfolio_stats(gmv["weights"], MU, COV, risk_free=0.03)
    tangency = PO.tangency_portfolio(MU, COV, risk_free=0.03)
    assert tangency["sharpe_ratio"] > gmv_stats["sharpe_ratio"]


def test_tangency_portfolio_weights_sum_to_one():
    out = PO.tangency_portfolio(MU, COV, risk_free=0.03)
    assert sum(out["weights"]) == pytest.approx(1.0)


def test_capital_allocation_line_slope_equals_tangency_sharpe_ratio():
    tangency = PO.tangency_portfolio(MU, COV, risk_free=0.03)
    cal = PO.capital_allocation_line(tangency, risk_free=0.03, target_volatilities=[0.0, 0.10])
    slope = (cal[1]["expected_return"] - cal[0]["expected_return"]) / (cal[1]["volatility"] - cal[0]["volatility"])
    assert slope == pytest.approx(tangency["sharpe_ratio"])
    assert cal[0]["expected_return"] == pytest.approx(0.03)  # zero volatility -> all risk-free


def test_portfolio_stats_matches_hand_calc_for_equal_weights():
    weights = [1 / 3, 1 / 3, 1 / 3]
    out = PO.portfolio_stats(weights, MU, COV, risk_free=0.03)
    assert out["expected_return"] == pytest.approx(sum(MU) / 3)


def test_from_dict_bundles_everything():
    d = {"mu": MU, "cov": COV, "global_minimum_variance": {}, "tangency": {"risk_free": 0.03},
         "capital_allocation_line": {"target_volatilities": [0.05]}, "portfolio_stats": {"weights": [1 / 3, 1 / 3, 1 / 3], "risk_free": 0.03}}
    out = PO.from_dict(d)
    assert "global_minimum_variance" in out and "tangency" in out and "capital_allocation_line" in out and "portfolio_stats" in out
