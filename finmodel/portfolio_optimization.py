"""Markowitz mean-variance portfolio optimization: the global minimum-variance portfolio, the Merton (1972)
closed-form efficient frontier, and the tangency (maximum-Sharpe) portfolio / Capital Allocation Line — real,
standard modern portfolio theory (CFI's own named "Efficient Frontier and CAL Template"; this toolkit's catalog
survey flags it as a real, uncovered title). Pure Python (Gauss-Jordan matrix inversion), no numpy/scipy
dependency, consistent with the rest of this toolkit — workable for the small (a handful of assets) portfolios a
CFI-style template targets, not a production portfolio-construction engine for hundreds of names.

Closed form (fully invested, no short-sale constraint — the standard textbook derivation, e.g. CFA/Elton-Gruber):
given expected returns mu and covariance matrix Sigma, let
    A = 1' Sigma^-1 1,  B = 1' Sigma^-1 mu,  C = mu' Sigma^-1 mu,  D = A C - B^2
the minimum-variance portfolio for a TARGET return R is
    w(R) = [(C - B R) / D] * (Sigma^-1 1)  +  [(A R - B) / D] * (Sigma^-1 mu)
and its variance is (A R^2 - 2 B R + C) / D — a parabola in (R, variance) space, the efficient frontier. Setting
R = B/A collapses this to the global minimum-variance portfolio w_gmv = (Sigma^-1 1) / A, verified as an internal
consistency check in tests/test_portfolio_optimization.py. The tangency portfolio (with a risk-free asset) is the
same closed form applied to EXCESS returns: w_tangency proportional to Sigma^-1 (mu - rf * 1)."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def _invert(matrix: Sequence[Sequence[float]]) -> List[List[float]]:
    """Gauss-Jordan elimination with partial pivoting -- a real, standard, numerically reasonable matrix inverse
    for the small (n <= a few dozen assets) covariance matrices this module targets."""
    n = len(matrix)
    aug = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            raise ValueError("covariance matrix is singular (or near-singular) -- check for duplicate/redundant assets")
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]
        for r in range(n):
            if r != col:
                factor = aug[r][col]
                aug[r] = [a - factor * b for a, b in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


def _matvec(matrix: Sequence[Sequence[float]], vec: Sequence[float]) -> List[float]:
    return [sum(m * v for m, v in zip(row, vec)) for row in matrix]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def portfolio_stats(weights: Sequence[float], mu: Sequence[float], cov: Sequence[Sequence[float]], risk_free: float = None) -> Dict[str, Any]:
    """Expected return, volatility, and (if risk_free is given) the Sharpe ratio for an arbitrary weight vector —
    useful to check a hand-picked or externally-supplied portfolio against this module's optimized ones."""
    expected_return = _dot(weights, mu)
    variance = _dot(weights, _matvec(cov, weights))
    volatility = variance ** 0.5
    out = {"weights": list(weights), "expected_return": expected_return, "variance": variance, "volatility": volatility}
    if risk_free is not None:
        out["sharpe_ratio"] = safe_div(expected_return - risk_free, volatility)
    return out


def global_minimum_variance_portfolio(cov: Sequence[Sequence[float]]) -> Dict[str, Any]:
    n = len(cov)
    inv = _invert(cov)
    ones = [1.0] * n
    num = _matvec(inv, ones)
    denom = sum(num)
    weights = [x / denom for x in num]
    variance = _dot(weights, _matvec(cov, weights))
    return {"weights": weights, "expected_return": None, "variance": variance, "volatility": variance ** 0.5}


def efficient_frontier(mu: Sequence[float], cov: Sequence[Sequence[float]], target_returns: Sequence[float]) -> List[Dict[str, Any]]:
    """The real Merton (1972) closed-form frontier: for each target expected return, the minimum-variance
    portfolio that achieves EXACTLY that return, weights summing to 1 (short sales allowed — the standard
    unconstrained textbook case; a long-only constraint would need numerical quadratic programming instead)."""
    n = len(cov)
    inv = _invert(cov)
    ones = [1.0] * n
    inv_ones = _matvec(inv, ones)
    inv_mu = _matvec(inv, mu)
    A = _dot(ones, inv_ones)
    B = _dot(ones, inv_mu)
    C = _dot(mu, inv_mu)
    D = A * C - B * B
    if abs(D) < 1e-12:
        raise ValueError("degenerate frontier (A*C == B^2) -- check that mu isn't proportional to a constant vector")
    points = []
    for target in target_returns:
        lam = (C - B * target) / D
        gam = (A * target - B) / D
        weights = [lam * a + gam * b for a, b in zip(inv_ones, inv_mu)]
        variance = _dot(weights, _matvec(cov, weights))
        points.append({"target_return": target, "weights": weights, "variance": variance, "volatility": variance ** 0.5})
    return points


def tangency_portfolio(mu: Sequence[float], cov: Sequence[Sequence[float]], risk_free: float) -> Dict[str, Any]:
    """The maximum-Sharpe-ratio portfolio of risky assets when a risk-free asset is available — the point where
    the Capital Allocation Line (a straight line from (0, risk_free) through this portfolio) is tangent to the
    efficient frontier. Same closed form as the frontier above, applied to EXCESS returns (mu - risk_free)."""
    n = len(cov)
    inv = _invert(cov)
    excess = [m - risk_free for m in mu]
    num = _matvec(inv, excess)
    denom = sum(num)
    weights = [x / denom for x in num]
    expected_return = _dot(weights, mu)
    variance = _dot(weights, _matvec(cov, weights))
    volatility = variance ** 0.5
    return {"weights": weights, "expected_return": expected_return, "variance": variance, "volatility": volatility,
            "sharpe_ratio": safe_div(expected_return - risk_free, volatility)}


def capital_allocation_line(tangency: Dict[str, Any], risk_free: float, target_volatilities: Sequence[float]) -> List[Dict[str, Any]]:
    """The CAL: mixing the risk-free asset with the tangency portfolio achieves any point along a straight line
    of slope = the tangency portfolio's Sharpe ratio — real, standard proof that no risky-only combination can
    beat this line (it's tangent to the frontier, not a chord through it)."""
    slope = tangency["sharpe_ratio"]
    points = []
    for vol in target_volatilities:
        expected_return = risk_free + slope * vol
        weight_in_tangency = safe_div(vol, tangency["volatility"])
        points.append({"volatility": vol, "expected_return": expected_return, "weight_in_tangency_portfolio": weight_in_tangency,
                       "weight_in_risk_free": 1 - weight_in_tangency})
    return points


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    mu = d.get("mu")
    cov = d.get("cov")
    if cov is not None and "global_minimum_variance" in d:
        out["global_minimum_variance"] = global_minimum_variance_portfolio(cov)
    if mu is not None and cov is not None and "efficient_frontier" in d:
        out["efficient_frontier"] = efficient_frontier(mu, cov, d["efficient_frontier"]["target_returns"])
    if mu is not None and cov is not None and "tangency" in d:
        out["tangency"] = tangency_portfolio(mu, cov, d["tangency"]["risk_free"])
        if "capital_allocation_line" in d:
            out["capital_allocation_line"] = capital_allocation_line(out["tangency"], d["tangency"]["risk_free"], d["capital_allocation_line"]["target_volatilities"])
    if mu is not None and cov is not None and "portfolio_stats" in d:
        p = d["portfolio_stats"]
        out["portfolio_stats"] = portfolio_stats(p["weights"], mu, cov, risk_free=p.get("risk_free"))
    return out
