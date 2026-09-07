"""Cap table / ESOP modeling: priced-round dilution (including the standard "option pool shuffle") and an exit
liquidation-preference waterfall — the cap-table-management and ESOP-design work real CFO-services firms (e.g.
Flipcarbon's "ESOP Scheme Design", fractional-CFO cap table work) and VC funds do routinely for portfolio
companies, distilled to the standard mechanics documented in Y Combinator's SAFE/equity primers, Brad Feld &
Jason Mendelson's *Venture Deals*, and Carta's own cap-table methodology notes.

Two real, easy-to-get-wrong mechanics this module gets right on purpose:

1. The option pool "shuffle": a term sheet specifying a target *post-financing* option pool percentage carves
   that pool out of the PRE-money valuation, so it dilutes only existing holders, not the new investor. Solving
   for the correct pool top-up requires simultaneous equations (the pool and the new investor's shares are both
   priced off the same per-share price, which itself depends on the pool top-up) — `_option_pool_topup()` below
   is the closed-form solution, verified in tests/test_cap_table.py to reproduce the new investor's exact
   intended post-money ownership (investment / post-money) regardless of the pool target.
2. Non-participating preferred stock's conversion decision at exit: a non-participating holder gets the GREATER
   of its liquidation preference or its as-converted pro-rata share of the full proceeds — never both, and never
   automatically the preference (a common modeling mistake). Participating preferred gets its preference AND
   then also participates pro-rata in the remainder alongside common — the real "double-dip".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


@dataclass
class Holder:
    name: str
    shares: float
    security: str = "common"      # "common" | "preferred" | "option_pool"
    round_name: str = ""          # which round created these shares; "" for pre-existing holders
    invested: float = 0.0         # cash invested for these shares (preferred only; drives the liquidation preference)
    liquidation_preference_multiple: float = 1.0
    participating: bool = False
    seniority: int = 0            # higher pays out first in the exit waterfall; ties share pro-rata within the tier


@dataclass
class Round:
    name: str
    pre_money: float
    investment: float
    target_option_pool_pct: Optional[float] = None   # post-financing fully-diluted %, or None to skip the shuffle
    investor_name: str = ""
    liquidation_preference_multiple: float = 1.0
    participating: bool = False
    seniority: Optional[int] = None                  # defaults to 1 + the highest existing seniority (newest = senior)


@dataclass
class CapTableResult:
    rounds_applied: List[Dict[str, Any]]
    holders: List[Holder]

    def ownership(self) -> Dict[str, float]:
        total = sum(h.shares for h in self.holders)
        out: Dict[str, float] = {}
        for h in self.holders:
            out[h.name] = out.get(h.name, 0.0) + safe_div(h.shares, total)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"rounds_applied": self.rounds_applied,
                "holders": [dict(name=h.name, shares=h.shares, security=h.security, round_name=h.round_name,
                                 invested=h.invested, liquidation_preference_multiple=h.liquidation_preference_multiple,
                                 participating=h.participating, seniority=h.seniority) for h in self.holders],
                "ownership": self.ownership()}


def _option_pool_topup(n0: float, existing_pool: float, pre_money: float, investment: float, target_pct: float) -> float:
    """Closed-form solution for the pre-money option-pool top-up. Let N1 = n0 + topup (fully-diluted shares just
    after the top-up, before the new investor); price P = pre_money / N1; new investor shares = investment / P;
    N2 = N1 * (pre_money + investment) / pre_money (post-financing fully-diluted). Solving
    (existing_pool + topup) = target_pct * N2 for topup gives the formula below (k = target_pct * post_money /
    pre_money must be < 1, i.e. the target pool can't exceed 100% of the pre-money-side capitalization)."""
    post_money = pre_money + investment
    k = target_pct * post_money / pre_money
    if k >= 1:
        raise ValueError(f"target_option_pool_pct={target_pct:.1%} is infeasible for this pre-money/investment ratio (k={k:.3f} >= 1)")
    return (k * n0 - existing_pool) / (1 - k)


def simulate_rounds(initial_holders: Sequence[Holder], rounds: Sequence[Round]) -> CapTableResult:
    """Applies each round in order: pool shuffle (if requested) dilutes existing holders pre-money, then the new
    investor buys in at the resulting per-share price. Returns the final holder list plus a per-round audit
    trail (price per share, pool top-up, new investor shares, post-money ownership actually achieved)."""
    holders: List[Holder] = [Holder(**vars(h)) for h in initial_holders]
    rounds_applied: List[Dict[str, Any]] = []
    for rnd in rounds:
        n0 = sum(h.shares for h in holders)
        pool_holders = [h for h in holders if h.security == "option_pool"]
        existing_pool = sum(h.shares for h in pool_holders)
        topup = 0.0
        if rnd.target_option_pool_pct is not None:
            topup = _option_pool_topup(n0, existing_pool, rnd.pre_money, rnd.investment, rnd.target_option_pool_pct)
            if topup > 0:
                if pool_holders:
                    pool_holders[0].shares += topup
                else:
                    holders.append(Holder(name="Option pool", shares=topup, security="option_pool", round_name=rnd.name))
        n1 = n0 + max(topup, 0.0)
        price_per_share = rnd.pre_money / n1
        new_shares = rnd.investment / price_per_share
        seniority = rnd.seniority if rnd.seniority is not None else 1 + max((h.seniority for h in holders if h.security == "preferred"), default=0)
        investor_name = rnd.investor_name or f"{rnd.name} investor"
        holders.append(Holder(name=investor_name, shares=new_shares, security="preferred", round_name=rnd.name,
                              invested=rnd.investment, liquidation_preference_multiple=rnd.liquidation_preference_multiple,
                              participating=rnd.participating, seniority=seniority))
        post_money = rnd.pre_money + rnd.investment
        n2 = n1 + new_shares
        rounds_applied.append({"round": rnd.name, "pre_money": rnd.pre_money, "investment": rnd.investment,
                               "post_money": post_money, "price_per_share": price_per_share,
                               "option_pool_topup": topup, "new_investor_shares": new_shares,
                               "fully_diluted_shares_post": n2,
                               "new_investor_ownership_pct": safe_div(new_shares, n2),
                               "new_investor_ownership_pct_intended": safe_div(rnd.investment, post_money)})
    return CapTableResult(rounds_applied=rounds_applied, holders=holders)


def exit_waterfall(cap_table: CapTableResult, exit_proceeds: float) -> Dict[str, Any]:
    """Standard liquidation-preference waterfall: preferred tiers are paid out senior-to-junior (highest
    `seniority` first); within a tier, non-participating holders take the GREATER of their preference or their
    as-converted pro-rata share of the FULL exit proceeds (computed once, up front, against total fully-diluted
    shares); participating holders take their preference off the top AND THEN also share pro-rata in whatever
    proceeds remain after every tier's preferences are paid, alongside common. Common (and any preferred that
    chose to convert) splits the final remainder pro-rata by share count."""
    total_shares = sum(h.shares for h in cap_table.holders)
    remaining = exit_proceeds
    payouts: Dict[str, float] = {h.name: 0.0 for h in cap_table.holders}
    converted: List[Holder] = []           # non-participating holders who chose as-converted instead of their preference
    participating_remainder: List[Holder] = []  # participating holders who take a preference AND share the remainder
    preferred = [h for h in cap_table.holders if h.security == "preferred"]
    for tier in sorted({h.seniority for h in preferred}, reverse=True):
        tier_holders = [h for h in preferred if h.seniority == tier]
        for h in tier_holders:
            preference = min(h.invested * h.liquidation_preference_multiple, remaining)
            as_converted = exit_proceeds * safe_div(h.shares, total_shares)
            if h.participating:
                payouts[h.name] += preference
                remaining -= preference
                participating_remainder.append(h)
            elif as_converted > preference:
                converted.append(h)  # decide later, once we know what "the remainder" is — see below
            else:
                payouts[h.name] += preference
                remaining -= preference
    # remaining proceeds split pro-rata among: common, option pool, any converted preferred, and participating
    # preferred's second dip — all "as-converted" shares
    sharing_pool = [h for h in cap_table.holders if h.security in ("common", "option_pool")] + converted + participating_remainder
    sharing_shares = sum(h.shares for h in sharing_pool)
    for h in sharing_pool:
        payouts[h.name] += remaining * safe_div(h.shares, sharing_shares)
    return {"exit_proceeds": exit_proceeds, "payouts": payouts,
            "converted_to_common": [h.name for h in converted],
            "participating_tiers": sorted({h.seniority for h in participating_remainder})}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    initial = [Holder(**h) for h in d["initial_holders"]]
    rounds = [Round(**r) for r in d["rounds"]]
    result = simulate_rounds(initial, rounds)
    out: Dict[str, Any] = {"cap_table": result.to_dict()}
    if "exit_proceeds" in d:
        out["exit_waterfall"] = exit_waterfall(result, d["exit_proceeds"])
    return out
