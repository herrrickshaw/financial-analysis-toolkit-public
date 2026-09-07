"""finmodel.options: Black-Scholes is checked against Hull's own textbook reference case, put-call parity is
checked both for a case that holds and one that's a real, tradeable arbitrage, the Greeks are cross-checked
against their known analytic relationships (not just plausibility), and implied volatility round-trips a price
back to the vol that produced it."""
import math

import pytest

from finmodel import options as O


def test_black_scholes_matches_textbook_reference_case():
    # Hull's own reference example: S=K=100, r=5%, vol=20%, T=1yr -> call ~10.45, put ~5.57
    call = O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="call")
    put = O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="put")
    assert call["price"] == pytest.approx(10.4506, abs=1e-3)
    assert put["price"] == pytest.approx(5.5735, abs=1e-3)


def test_deep_itm_call_converges_to_intrinsic_value_as_time_shrinks():
    call = O.black_scholes(spot=150, strike=100, rate=0.05, vol=0.20, time=1e-4, option_type="call")
    assert call["price"] == pytest.approx(150 - 100 * (1 - 0.05 * 1e-4), abs=0.1)


def test_invalid_option_type_raises():
    with pytest.raises(ValueError):
        O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.2, time=1.0, option_type="straddle")


def test_zero_time_or_vol_raises():
    with pytest.raises(ValueError):
        O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.0, time=1.0)
    with pytest.raises(ValueError):
        O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.2, time=0.0)


def test_put_call_parity_holds_for_consistent_black_scholes_prices():
    call = O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="call")["price"]
    put = O.black_scholes(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="put")["price"]
    out = O.put_call_parity_check(call, put, spot=100, strike=100, rate=0.05, time=1.0)
    assert out["holds"] is True
    assert out["arbitrage_gap"] == pytest.approx(0.0, abs=1e-6)


def test_put_call_parity_flags_a_real_mispricing():
    # a call quoted $2 too high relative to its put -- a real, tradeable conversion arbitrage
    out = O.put_call_parity_check(call_price=12.4506, put_price=5.5735, spot=100, strike=100, rate=0.05, time=1.0)
    assert out["holds"] is False
    assert out["arbitrage_gap"] == pytest.approx(2.0, abs=1e-3)


def test_call_delta_is_between_zero_and_one_put_delta_between_minus_one_and_zero():
    g_call = O.greeks(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="call")
    g_put = O.greeks(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="put")
    assert 0 < g_call["delta"] < 1
    assert -1 < g_put["delta"] < 0
    # a real, exact identity: call delta - put delta = e^(-qT) (=1 here, q=0)
    assert g_call["delta"] - g_put["delta"] == pytest.approx(1.0, abs=1e-9)


def test_gamma_and_vega_are_identical_for_call_and_put_at_the_same_strike():
    # a real, standard Black-Scholes property -- gamma and vega don't depend on option_type
    g_call = O.greeks(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="call")
    g_put = O.greeks(spot=100, strike=100, rate=0.05, vol=0.20, time=1.0, option_type="put")
    assert g_call["gamma"] == pytest.approx(g_put["gamma"])
    assert g_call["vega"] == pytest.approx(g_put["vega"])


def test_implied_volatility_recovers_the_input_vol():
    price = O.black_scholes(spot=100, strike=105, rate=0.03, vol=0.25, time=0.5, option_type="put")["price"]
    iv = O.implied_volatility(price, spot=100, strike=105, rate=0.03, time=0.5, option_type="put")
    assert iv == pytest.approx(0.25, abs=1e-4)


def test_from_dict_bundles_black_scholes_greeks_and_parity():
    d = {"black_scholes": {"spot": 100, "strike": 100, "rate": 0.05, "vol": 0.2, "time": 1.0, "option_type": "call"},
         "put_call_parity": {"call_price": 10.4506, "put_price": 5.5735, "spot": 100, "strike": 100, "rate": 0.05, "time": 1.0, "tol": 0.001}}
    out = O.from_dict(d)
    assert "black_scholes" in out and "greeks" in out and out["put_call_parity"]["holds"] is True


def test_geometric_asian_option_adjusted_parameters_match_the_derivation():
    spot, strike, rate, vol, time, q = 100.0, 100.0, 0.05, 0.30, 1.0, 0.0
    out = O.geometric_asian_option(spot, strike, rate, vol, time, q, "call")
    assert out["adjusted_volatility"] == pytest.approx(vol / 3 ** 0.5)
    assert out["effective_cost_of_carry"] == pytest.approx(0.5 * (rate - q) - vol ** 2 / 12)


def test_geometric_asian_option_matches_independent_monte_carlo_simulation():
    # an independent numerical check (not merely the closed form agreeing with itself): simulate the
    # discretized geometric average along many GBM paths and confirm the closed form lands within a few
    # percent of the simulated price.
    import random

    spot, strike, rate, vol, time, q = 100.0, 100.0, 0.05, 0.30, 1.0, 0.0
    random.seed(42)
    n_paths, n_steps = 20_000, 50
    dt = time / n_steps
    drift = (rate - q - 0.5 * vol * vol) * dt
    vol_dt = vol * dt ** 0.5
    total_payoff = 0.0
    for _ in range(n_paths):
        log_s = math.log(spot)
        log_sum = 0.0
        for _step in range(n_steps):
            log_s += drift + vol_dt * random.gauss(0, 1)
            log_sum += log_s
        geo_avg = math.exp(log_sum / n_steps)
        total_payoff += max(geo_avg - strike, 0.0)
    mc_price = math.exp(-rate * time) * total_payoff / n_paths

    closed_form_price = O.geometric_asian_option(spot, strike, rate, vol, time, q, "call")["price"]
    assert closed_form_price == pytest.approx(mc_price, rel=0.05)


def test_geometric_asian_option_is_cheaper_than_the_vanilla_european_option():
    # a real, well-known property: averaging reduces effective volatility, so an average-price option is
    # always cheaper than the vanilla European option struck at the same level.
    kwargs = dict(spot=100.0, strike=100.0, rate=0.05, vol=0.30, time=1.0)
    vanilla = O.black_scholes(**kwargs, option_type="call")["price"]
    asian = O.geometric_asian_option(**kwargs, option_type="call")["price"]
    assert asian < vanilla


def test_geometric_asian_from_dict():
    out = O.from_dict({"geometric_asian_option": {"spot": 100.0, "strike": 100.0, "rate": 0.05, "vol": 0.3, "time": 1.0}})
    assert out["geometric_asian_option"]["price"] > 0
