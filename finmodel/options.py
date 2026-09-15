"""Black-Scholes-Merton option pricing, the Greeks, and put-call parity — real, standard closed-form derivatives
pricing (CFI's own named "Black Scholes Calculator" and "Put Call Parity Calculator" templates; this toolkit's
catalog — `finmodel catalog list --source cfi` — flags these as real, uncovered titles). Pure Python (the normal
CDF via `math.erf`), no numpy/scipy dependency, consistent with the rest of this toolkit.

  Black-Scholes-Merton (dividend-adjusted, q=0 reduces to the plain Black-Scholes case):
    d1 = (ln(S/K) + (r - q + sigma^2/2) T) / (sigma sqrt(T));  d2 = d1 - sigma sqrt(T)
    Call = S e^(-qT) N(d1) - K e^(-rT) N(d2)
    Put  = K e^(-rT) N(-d2) - S e^(-qT) N(-d1)
  Put-call parity (the no-arbitrage identity the Put Call Parity Calculator checks):
    C - P = S e^(-qT) - K e^(-rT)"""
from __future__ import annotations

import math
from typing import Any, Dict


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def norm_pdf(x: float) -> float:
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def _d1_d2(spot: float, strike: float, rate: float, vol: float, time: float, dividend_yield: float = 0.0) -> tuple:
    if time <= 0 or vol <= 0:
        raise ValueError("time and vol must both be positive")
    d1 = (math.log(spot / strike) + (rate - dividend_yield + vol ** 2 / 2) * time) / (vol * math.sqrt(time))
    d2 = d1 - vol * math.sqrt(time)
    return d1, d2


def black_scholes(spot: float, strike: float, rate: float, vol: float, time: float, dividend_yield: float = 0.0,
                  option_type: str = "call") -> Dict[str, Any]:
    """option_type: 'call' | 'put'. time is in years, rate/vol/dividend_yield are annualized decimals."""
    d1, d2 = _d1_d2(spot, strike, rate, vol, time, dividend_yield)
    disc_div = math.exp(-dividend_yield * time)
    disc_r = math.exp(-rate * time)
    if option_type == "call":
        price = spot * disc_div * norm_cdf(d1) - strike * disc_r * norm_cdf(d2)
    elif option_type == "put":
        price = strike * disc_r * norm_cdf(-d2) - spot * disc_div * norm_cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    return {"price": price, "d1": d1, "d2": d2, "option_type": option_type,
            "inputs": {"spot": spot, "strike": strike, "rate": rate, "vol": vol, "time": time, "dividend_yield": dividend_yield}}


def greeks(spot: float, strike: float, rate: float, vol: float, time: float, dividend_yield: float = 0.0,
          option_type: str = "call") -> Dict[str, float]:
    """Per-unit-underlying sensitivities. Vega and rho are per 1.00 (100 percentage points) of vol/rate — divide
    by 100 for the conventional "per 1% move" quoting convention."""
    d1, d2 = _d1_d2(spot, strike, rate, vol, time, dividend_yield)
    disc_div = math.exp(-dividend_yield * time)
    disc_r = math.exp(-rate * time)
    sqrt_t = math.sqrt(time)
    gamma = disc_div * norm_pdf(d1) / (spot * vol * sqrt_t)
    vega = spot * disc_div * norm_pdf(d1) * sqrt_t
    if option_type == "call":
        delta = disc_div * norm_cdf(d1)
        theta = (-(spot * disc_div * norm_pdf(d1) * vol) / (2 * sqrt_t) - rate * strike * disc_r * norm_cdf(d2) + dividend_yield * spot * disc_div * norm_cdf(d1))
        rho = strike * time * disc_r * norm_cdf(d2)
    elif option_type == "put":
        delta = disc_div * (norm_cdf(d1) - 1)
        theta = (-(spot * disc_div * norm_pdf(d1) * vol) / (2 * sqrt_t) + rate * strike * disc_r * norm_cdf(-d2) - dividend_yield * spot * disc_div * norm_cdf(-d1))
        rho = -strike * time * disc_r * norm_cdf(-d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}


def put_call_parity_check(call_price: float, put_price: float, spot: float, strike: float, rate: float, time: float,
                          dividend_yield: float = 0.0, tol: float = 1e-6) -> Dict[str, Any]:
    """The no-arbitrage identity a market maker checks before trading: C - P should equal the synthetic forward
    S e^(-qT) - K e^(-rT). A nonzero `arbitrage_gap` beyond `tol` flags a real, tradeable mispricing (a
    conversion/reversal arbitrage), before transaction costs."""
    lhs = call_price - put_price
    rhs = spot * math.exp(-dividend_yield * time) - strike * math.exp(-rate * time)
    gap = lhs - rhs
    return {"lhs_call_minus_put": lhs, "rhs_synthetic_forward": rhs, "arbitrage_gap": gap, "holds": abs(gap) <= tol}


def implied_volatility(option_price: float, spot: float, strike: float, rate: float, time: float, dividend_yield: float = 0.0,
                       option_type: str = "call", lo: float = 1e-6, hi: float = 5.0, tol: float = 1e-8, max_iter: int = 100) -> float:
    """Bisection on Black-Scholes' vol input — monotonic in vol (real property, Vega > 0), so bisection always
    converges without needing a derivative-based (Newton) solver."""
    def price_at(vol):
        return black_scholes(spot, strike, rate, vol, time, dividend_yield, option_type)["price"]
    if price_at(lo) > option_price or price_at(hi) < option_price:
        raise ValueError("option_price is outside the range spanned by vol in [lo, hi] -- check inputs for an arbitrage violation")
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if price_at(mid) < option_price:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def geometric_asian_option(spot: float, strike: float, rate: float, vol: float, time: float,
                           dividend_yield: float = 0.0, option_type: str = "call") -> Dict[str, Any]:
    """Closed-form price of a European option on the CONTINUOUS geometric average of the underlying's price
    path (Kemna & Vorst, 1990) -- flagged as a real, bounded exotic-derivative gap in
    `docs/PROFESSOR_COURSE_SURVEY.md`'s "FX structured-product origination" deferral, and resolved here with
    a self-contained derivation rather than a memorized formula.

    Under risk-neutral GBM, ln(S_t) = ln(S_0) + (rate - dividend_yield - vol^2/2) t + vol * W_t. The
    continuous geometric average is G = exp((1/T) INT[0,T] ln(S_t) dt); since INT[0,T] W_t dt is itself
    Gaussian with variance T^3/3 (a standard result for integrated Brownian motion), (1/T) INT[0,T] W_t dt has
    variance T/3. So ln(G) is normal with variance vol^2 * T / 3 -- i.e. G is lognormal with an EFFECTIVE
    volatility `vol_A = vol / sqrt(3)`. Matching the mean of ln(G) to a standard risk-neutral lognormal
    process with that volatility gives an effective cost of carry `b_A = 0.5*(rate - dividend_yield) -
    vol^2/12`. The option is then priced EXACTLY by this module's own `black_scholes()`, called with
    `vol_A` and an implied dividend yield of `rate - b_A` -- no new pricing machinery, just the derived
    adjustment to two inputs. Verified in this module's own test suite against an independent Monte Carlo
    simulation of the discretized geometric average, not merely against the closed form's own internal
    consistency."""
    vol_a = vol / math.sqrt(3)
    b_a = 0.5 * (rate - dividend_yield) - vol ** 2 / 12
    implied_dividend_yield = rate - b_a
    bs = black_scholes(spot, strike, rate, vol_a, time, implied_dividend_yield, option_type)
    return {"price": bs["price"], "option_type": option_type, "adjusted_volatility": vol_a, "effective_cost_of_carry": b_a,
            "inputs": {"spot": spot, "strike": strike, "rate": rate, "vol": vol, "time": time, "dividend_yield": dividend_yield}}


_BARRIER_TYPES = ("down-and-out", "down-and-in", "up-and-out", "up-and-in")


def barrier_option(spot: float, strike: float, barrier: float, rate: float, vol: float, time: float,
                   dividend_yield: float = 0.0, option_type: str = "call",
                   barrier_type: str = "down-and-out", rebate: float = 0.0) -> Dict[str, Any]:
    """Closed-form price of a single continuously-monitored barrier option (Reiner & Rubinstein, 1991, as
    tabulated in Haug's 'The Complete Guide to Option Pricing Formulas', ch. 4.17) -- the other real,
    named exotic-derivative gap `docs/DEFERRED_GAPS_REVISITED.md` flagged and left deferred after
    `geometric_asian_option` ("their real closed forms have many more terms and a materially higher risk of
    transcription error without an equally solid verification method at hand"). Resolved the same way: the
    six component terms A/B/C/D/E/F below are combined into the 8 standard barrier payoffs exactly per
    Haug's table, then independently verified two ways in this module's own test suite -- against a real
    published worked example (not a self-referential check) and against a Monte Carlo simulation of a
    discretely-monitored path, plus the model-internal in/out parity identity (knock-in + knock-out price
    == the vanilla Black-Scholes price) that must hold exactly with no rebate.

    barrier_type: 'down-and-out' | 'down-and-in' | 'up-and-out' | 'up-and-in'. A down barrier must sit below
    the current spot and an up barrier above it -- an option already past its barrier is not a pricing
    question this formula answers. `rebate` (paid at expiry if a knock-out option is never knocked out, or a
    knock-in option is knocked out and never knocked in) defaults to 0, the common case."""
    if time <= 0 or vol <= 0:
        raise ValueError("time and vol must both be positive")
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'")
    if barrier_type not in _BARRIER_TYPES:
        raise ValueError(f"barrier_type must be one of {_BARRIER_TYPES}")
    is_down = barrier_type.startswith("down")
    if is_down and barrier >= spot:
        raise ValueError("a down barrier must be strictly below the current spot price")
    if not is_down and barrier <= spot:
        raise ValueError("an up barrier must be strictly above the current spot price")

    S, X, H, T, r, sigma, q, K = spot, strike, barrier, time, rate, vol, dividend_yield, rebate
    b = r - q
    sqrt_t = sigma * math.sqrt(T)
    mu = (b - sigma ** 2 / 2) / sigma ** 2
    lam = math.sqrt(mu ** 2 + 2 * r / sigma ** 2)
    x1 = math.log(S / X) / sqrt_t + (1 + mu) * sqrt_t
    x2 = math.log(S / H) / sqrt_t + (1 + mu) * sqrt_t
    y1 = math.log(H ** 2 / (S * X)) / sqrt_t + (1 + mu) * sqrt_t
    y2 = math.log(H / S) / sqrt_t + (1 + mu) * sqrt_t
    z = math.log(H / S) / sqrt_t + lam * sqrt_t

    phi = 1.0 if option_type == "call" else -1.0
    eta = 1.0 if is_down else -1.0
    disc_carry = math.exp((b - r) * T)   # = e^(-qT)
    disc_r = math.exp(-r * T)
    hs_ratio = H / S

    def term(x):
        return phi * S * disc_carry * norm_cdf(phi * x) - phi * X * disc_r * norm_cdf(phi * x - phi * sqrt_t)

    def term_reflected(y):
        return (phi * S * disc_carry * hs_ratio ** (2 * (mu + 1)) * norm_cdf(eta * y)
                - phi * X * disc_r * hs_ratio ** (2 * mu) * norm_cdf(eta * y - eta * sqrt_t))

    A = term(x1)
    B = term(x2)
    C = term_reflected(y1)
    D = term_reflected(y2)
    E = K * disc_r * (norm_cdf(eta * x2 - eta * sqrt_t) - hs_ratio ** (2 * mu) * norm_cdf(eta * y2 - eta * sqrt_t))
    F = K * (hs_ratio ** (mu + lam) * norm_cdf(eta * z) + hs_ratio ** (mu - lam) * norm_cdf(eta * z - 2 * eta * lam * sqrt_t))

    x_ge_h = X >= H
    if option_type == "call":
        price = {
            ("down-and-in", True): C + E, ("down-and-in", False): A - B + D + E,
            ("down-and-out", True): A - C + F, ("down-and-out", False): B - D + F,
            ("up-and-in", True): A + E, ("up-and-in", False): B - C + D + E,
            ("up-and-out", True): F, ("up-and-out", False): A - B + C - D + F,
        }[(barrier_type, x_ge_h)]
    else:
        price = {
            ("down-and-in", True): B - C + D + E, ("down-and-in", False): A + E,
            ("down-and-out", True): A - B + C - D + F, ("down-and-out", False): F,
            ("up-and-in", True): A - B + D + E, ("up-and-in", False): C + E,
            ("up-and-out", True): B - D + F, ("up-and-out", False): A - C + F,
        }[(barrier_type, x_ge_h)]

    vanilla = black_scholes(S, X, r, sigma, T, q, option_type)["price"]
    return {"price": price, "vanilla_price": vanilla, "option_type": option_type, "barrier_type": barrier_type,
            "inputs": {"spot": spot, "strike": strike, "barrier": barrier, "rate": rate, "vol": vol, "time": time,
                       "dividend_yield": dividend_yield, "rebate": rebate}}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "black_scholes" in d:
        p = d["black_scholes"]
        out["black_scholes"] = black_scholes(**p)
        out["greeks"] = greeks(**{k: v for k, v in p.items()})
    if "put_call_parity" in d:
        out["put_call_parity"] = put_call_parity_check(**d["put_call_parity"])
    if "implied_volatility" in d:
        out["implied_volatility"] = implied_volatility(**d["implied_volatility"])
    if "geometric_asian_option" in d:
        out["geometric_asian_option"] = geometric_asian_option(**d["geometric_asian_option"])
    if "barrier_option" in d:
        out["barrier_option"] = barrier_option(**d["barrier_option"])
    return out
