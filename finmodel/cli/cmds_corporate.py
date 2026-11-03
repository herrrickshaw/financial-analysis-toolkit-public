"""Strategy, accounting, insurance and corporate-finance commands."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import _load_json


def cmd_strategy(a):
    from .. import strategy_frameworks as SF
    res = SF.from_dict(_load_json(a.inputs))
    if "market_sizing_top_down" in res:
        m = res["market_sizing_top_down"]
        print(f"Market sizing (top-down): TAM {m['tam']:,.0f}  SAM {m['sam']:,.0f}  SOM {m['som']:,.0f}  (SOM = {m['som_pct_of_tam']:.2%} of TAM)")
    if "market_sizing_bottom_up" in res:
        m = res["market_sizing_bottom_up"]
        print(f"Market sizing (bottom-up): TAM {m['tam']:,.0f}  SOM {m['som']:,.0f}  (SOM = {m['som_pct_of_tam']:.2%} of TAM)")
        for s in m["segments"]:
            print(f"  {s['segment']:16} TAM {s['segment_tam']:>14,.0f}  SOM {s['segment_som']:>14,.0f}")
    if "bcg_matrix" in res:
        print("BCG Growth-Share Matrix:")
        for u in res["bcg_matrix"]["units"]:
            print(f"  {u['name']:16} rel. share {u['relative_market_share']:.2f}x  growth {u['market_growth_rate']:.1%}  → {u['classification']}")
    if "ge_mckinsey_matrix" in res:
        print("GE-McKinsey Nine-Box Matrix:")
        for u in res["ge_mckinsey_matrix"]["units"]:
            print(f"  {u['name']:16} attractiveness {u['industry_attractiveness_bucket']:6} ({u['industry_attractiveness_score']:.2f})  "
                  f"strength {u['business_strength_bucket']:6} ({u['business_strength_score']:.2f})  → {u['zone']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_ppa(a):
    from .. import ppa_valuation as PPA
    res = PPA.from_dict(_load_json(a.inputs))
    for src in ("relief_from_royalty", "mpeem", "cost_approach"):
        if src in res:
            for name, r in res[src].items():
                print(f"{src} — {name}: value {r['value']:,.0f}" + (f" (TAB factor {r['tab_factor']:.3f})" if "tab_factor" in r else ""))
    if "allocation" in res:
        al = res["allocation"]
        print(f"Allocation: intangibles {al['total_intangibles']:,.0f} + net identifiable assets {al['net_identifiable_assets_fair_value']:,.0f} "
              f"= {al['total_identifiable_assets']:,.0f}  →  goodwill {al['goodwill']:,.0f} ({al['goodwill_pct_of_price']:.1%} of price)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_impairment(a):
    from .. import impairment_testing as IT
    res = IT.from_dict(_load_json(a.inputs))
    if "goodwill" in res:
        r = res["goodwill"]
        print(f"Goodwill (ASC 350): impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}, remaining goodwill {r['remaining_goodwill']:,.0f}")
    if "indefinite_lived_intangible" in res:
        r = res["indefinite_lived_intangible"]
        print(f"Indefinite-lived intangible (ASC 350-30): impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}")
    if "long_lived_asset" in res:
        r = res["long_lived_asset"]
        print(f"Long-lived asset (ASC 360): Step 1 recoverable={r['step1_recoverable']}, impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_audit_analytics(a):
    from .. import audit_analytics as AA
    res = AA.from_dict(_load_json(a.inputs))
    if "benford" in res:
        b = res["benford"]
        print(f"Benford's Law (n={b['n']}): MAD {b['mad']:.4f} → {b['conformity']}")
    if "journal_entries" in res:
        j = res["journal_entries"]
        print(f"Journal entry testing: {j['n_flagged']}/{j['n_entries']} entries flagged")
        for f in j["flagged"]:
            print(f"  {f.get('id', '?'):>6}  amount {f.get('amount', 0):>12,.0f}  flags: {', '.join(f['flags'])}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_options(a):
    from .. import options as O
    res = O.from_dict(_load_json(a.inputs))
    if "black_scholes" in res:
        r = res["black_scholes"]
        print(f"{r['option_type'].capitalize()} price: {r['price']:.4f}  (d1={r['d1']:.4f}, d2={r['d2']:.4f})")
    if "greeks" in res:
        g = res["greeks"]
        print(f"Greeks: delta {g['delta']:.4f}  gamma {g['gamma']:.4f}  vega {g['vega']:.4f}  theta {g['theta']:.4f}  rho {g['rho']:.4f}")
    if "put_call_parity" in res:
        p = res["put_call_parity"]
        print(f"Put-call parity: C-P={p['lhs_call_minus_put']:.4f} vs synthetic forward {p['rhs_synthetic_forward']:.4f}  →  holds={p['holds']} (gap {p['arbitrage_gap']:.6f})")
    if "implied_volatility" in res:
        print(f"Implied volatility: {res['implied_volatility']:.4%}")
    if "geometric_asian_option" in res:
        r = res["geometric_asian_option"]
        print(f"Geometric Asian {r['option_type']}: {r['price']:.4f}  (adjusted vol {r['adjusted_volatility']:.4f}, cost of carry {r['effective_cost_of_carry']:.4f})")
    if "barrier_option" in res:
        r = res["barrier_option"]
        print(f"{r['barrier_type']} {r['option_type']}: {r['price']:.4f}  (vanilla {r['vanilla_price']:.4f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_project_finance(a):
    from .. import project_finance as PF
    res = PF.from_dict(_load_json(a.inputs))
    if "size_debt_by_dscr" in res:
        r = res["size_debt_by_dscr"]
        print(f"Debt sized to target DSCR {r['target_dscr']:.2f}x: max debt {r['max_debt_sized']:,.0f}")
    if "sculpted_amortization" in res:
        r = res["sculpted_amortization"]
        for i, row in enumerate(r["schedule"], 1):
            print(f"  period {i}: CFADS {row['cfads']:>12,.0f}  debt service {row['debt_service']:>12,.0f}  DSCR {row['dscr']:.2f}x  closing balance {row['closing_balance']:>12,.0f}")
        print(f"Fully repaid: {r['fully_repaid']}")
    if "llcr" in res:
        print(f"LLCR: {res['llcr']['llcr']:.2f}x")
    if "cap_rate_valuation" in res:
        print(f"Cap rate valuation: NOI {res['cap_rate_valuation']['noi']:,.0f} / {res['cap_rate_valuation']['cap_rate']:.2%}  →  value {res['cap_rate_valuation']['value']:,.0f}")
    if "levered_cash_on_cash" in res:
        print(f"Cash-on-cash return: {res['levered_cash_on_cash']['cash_on_cash_return']:.2%}")
    if "level_annuity_schedule" in res:
        r = res["level_annuity_schedule"]
        print(f"Level annuity: payment {r['level_payment']:,.0f}/yr, total interest {r['total_interest']:,.0f}")
    if "interest_only_bullet_schedule" in res:
        r = res["interest_only_bullet_schedule"]
        print(f"Interest-only + bullet: total interest {r['total_interest']:,.0f}, bullet {r['bullet_principal']:,.0f} at maturity")
    if "balloon_coverage_ratio" in res:
        print(f"Balloon coverage: {res['balloon_coverage_ratio']['coverage_ratio']:.2f}x")
    if "compare_debt_structures" in res:
        print("Debt structure comparison:")
        for name, s in res["compare_debt_structures"].items():
            print(f"  {name:20} total interest {s['total_interest']:>12,.0f}  year-1 debt service {s['year1_debt_service']:>12,.0f}  min DSCR {s['min_dscr']:.2f}x  avg DSCR {s['average_dscr']:.2f}x")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_dcf_diagnostics(a):
    from .. import dcf as D
    d = _load_json(a.inputs)
    out = D.check_unlevered_tax_consistency(d["ebit"], d["cash_taxes_used"], d["tax_rate"], tolerance=d.get("tolerance", 0.01))
    print(f"Likely uses levered (double-counted-shield) tax in an unlevered FCF: {out['likely_uses_levered_tax']}")
    if out["flagged_periods"]:
        print(f"Flagged periods (0-indexed): {out['flagged_periods']}")
    print(f"Total gap vs. a correctly unlevered tax build (undiscounted): {out['total_gap_undiscounted']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(out, indent=1))


def cmd_portfolio(a):
    from .. import portfolio_optimization as PO
    res = PO.from_dict(_load_json(a.inputs))
    if "global_minimum_variance" in res:
        r = res["global_minimum_variance"]
        print(f"Global minimum-variance portfolio: weights {['%.2f%%' % (w*100) for w in r['weights']]}  vol {r['volatility']:.2%}")
    if "efficient_frontier" in res:
        print("Efficient frontier:")
        for p in res["efficient_frontier"]:
            print(f"  target return {p['target_return']:.2%}  →  vol {p['volatility']:.2%}  weights {['%.2f%%' % (w*100) for w in p['weights']]}")
    if "tangency" in res:
        t = res["tangency"]
        print(f"Tangency portfolio: weights {['%.2f%%' % (w*100) for w in t['weights']]}  return {t['expected_return']:.2%}  vol {t['volatility']:.2%}  Sharpe {t['sharpe_ratio']:.3f}")
    if "capital_allocation_line" in res:
        print("Capital Allocation Line:")
        for p in res["capital_allocation_line"]:
            print(f"  vol {p['volatility']:.2%}  →  return {p['expected_return']:.2%}  ({p['weight_in_tangency_portfolio']:.1%} in tangency, {p['weight_in_risk_free']:.1%} in risk-free)")
    if "portfolio_stats" in res:
        s = res["portfolio_stats"]
        print(f"Portfolio: return {s['expected_return']:.2%}  vol {s['volatility']:.2%}" + (f"  Sharpe {s['sharpe_ratio']:.3f}" if "sharpe_ratio" in s else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_restructuring(a):
    from .. import restructuring as R
    res = R.from_dict(_load_json(a.inputs))
    if "recovery_waterfall" in res:
        wf = res["recovery_waterfall"]
        print(f"Recovery waterfall (reorg value {wf['reorg_value']:,.0f}):")
        for t in wf["tranches"]:
            print(f"  {t['name']:28} seniority {t['seniority']}  claim {t['claim_amount']:>14,.0f}  recovery {t['recovery']:>14,.0f}  ({t['recovery_pct']:.1%})")
        print(f"  Residual to equity: {wf['residual_to_equity']:,.0f}")
    if "fulcrum_security" in res:
        f = res["fulcrum_security"]
        print(f"Fulcrum security: {f['name']}" + (f" ({f['recovery_pct']:.1%} recovery)" if f.get("name") else f" — {f.get('note')}"))
    if "absolute_priority_check" in res:
        c = res["absolute_priority_check"]
        print(f"Absolute priority respected: {c['absolute_priority_respected']}" + (f"  departures: {c['departures']}" if c["departures"] else ""))
    if "dip_financing_sizing" in res:
        d = res["dip_financing_sizing"]
        print(f"DIP financing required: {d['required_dip_facility']:,.0f} (minimum projected cash {d['minimum_projected_cash']:,.0f} vs covenant {d['minimum_liquidity_covenant']:,.0f})")
    if "post_emergence_capital_structure" in res:
        p = res["post_emergence_capital_structure"]
        print(f"Post-emergence new debt: {p['new_debt']:,.0f} ({p['target_net_debt_to_ebitda']:.2f}x EBITDA {p['emergence_ebitda']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_bank_model(a):
    from .. import bank_model as B
    res = B.from_dict(_load_json(a.inputs))
    if "income_statement" in res:
        r = res["income_statement"]
        print(f"NII {r['nii']:,.0f} (NIM {r['nim']:.2%})  provision {r['provision']:,.0f}  efficiency ratio {r['efficiency_ratio']:.1%}  net income {r['net_income']:,.0f}")
    if "projection" in res:
        for row in res["projection"]:
            print(f"  year {row['year']}: NII {row['nii']:>14,.0f}  net income {row['net_income']:>14,.0f}  efficiency ratio {row['efficiency_ratio']:.1%}")
    if "regulatory_capital_ratios" in res:
        r = res["regulatory_capital_ratios"]
        print(f"CET1 {r['cet1_ratio']:.2%}  Tier1 {r['tier1_ratio']:.2%}  Total capital {r['total_capital_ratio']:.2%}  leverage {r['leverage_ratio']:.2%}  well-capitalized={r['well_capitalized']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_cohort_analysis(a):
    from .. import cohort_analysis as C
    res = C.from_dict(_load_json(a.inputs))
    if "retention_curve" in res:
        print(f"Retention curve: {['%.1f%%' % (p*100) for p in res['retention_curve']['retention_pct']]}")
    if "ltv_from_retention_curve" in res:
        print(f"LTV (from retention curve): {res['ltv_from_retention_curve']['ltv']:,.2f}")
    if "ltv_simplified" in res:
        print(f"LTV (simplified, ARPU x margin / churn): {res['ltv_simplified']['ltv']:,.2f}  (avg lifetime {res['ltv_simplified']['average_customer_lifetime_months']:.1f} months)")
    if "revenue_retention" in res:
        r = res["revenue_retention"]
        print(f"GRR {r['gross_revenue_retention']:.1%}  NRR {r['net_revenue_retention']:.1%}")
    if "ltv_to_cac" in res:
        print(f"LTV:CAC ratio: {res['ltv_to_cac']['ratio']:.2f}x")
    if "cac_payback_months" in res:
        print(f"CAC payback: {res['cac_payback_months']['cac_payback_months']:.1f} months")
    if "cohort_revenue_projection" in res:
        print(f"Cohort revenue by period: {['%.0f' % v for v in res['cohort_revenue_projection']['revenue_by_period']]}  total {res['cohort_revenue_projection']['total_revenue']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_insurance_pricing(a):
    from .. import insurance_pricing as I
    res = I.from_dict(_load_json(a.inputs))
    if "combined_ratio" in res:
        r = res["combined_ratio"]
        print(f"Loss ratio {r['loss_ratio']:.1%}  expense ratio {r['expense_ratio']:.1%}  combined ratio {r['combined_ratio']:.1%}  underwriting profitable={r['underwriting_profitable']}")
    if "operating_ratio" in res:
        r = res["operating_ratio"]
        print(f"Operating ratio {r['operating_ratio']:.1%}  overall profitable={r['overall_profitable']}")
    if "rate_making_premium" in res:
        r = res["rate_making_premium"]
        print(f"Gross premium: {r['gross_premium']:,.2f}  (loss cost multiplier {r['loss_cost_multiplier']:.3f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_convertible_bonds(a):
    from .. import convertible_bonds as CB
    res = CB.from_dict(_load_json(a.inputs))
    if "bond_floor" in res:
        print(f"Bond floor: {res['bond_floor']['bond_floor']:,.2f}")
    if "convertible_bond_value" in res:
        v = res["convertible_bond_value"]
        print(f"Conversion ratio {v['conversion_ratio']:.2f}  bond floor {v['bond_floor']:,.2f}  option value {v['option_value']:,.2f}  "
              f"conversion value {v['conversion_value']:,.2f}  estimated value {v['estimated_value']:,.2f}")
    if "conversion_premium" in res:
        print(f"Conversion premium: {res['conversion_premium']:.2%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_cmo(a):
    from .. import cmo as C
    res = C.from_dict(_load_json(a.inputs))
    if "cmo_deal" in res:
        r = res["cmo_deal"]
        print(f"Pool fully amortizes in {len(r['pool_cash_flows'])} months at {r['psa_pct']:.0%} PSA")
        for name, wal in r["weighted_average_life"].items():
            print(f"  Tranche {name}: WAL {wal:.2f} years")
    if "psa_sensitivity" in res:
        print("PSA sensitivity (Weighted Average Life by tranche):")
        for speed, wal in res["psa_sensitivity"].items():
            print(f"  {speed:>8}: " + "  ".join(f"{name} {w:.2f}y" for name, w in wal.items()))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_variance_analysis(a):
    from .. import variance_analysis as V
    res = V.from_dict(_load_json(a.inputs))
    if "budget_vs_actual_variance" in res:
        r = res["budget_vs_actual_variance"]
        print(f"Budget {r['budget_total']:,.0f}  actual {r['actual_total']:,.0f}  →  total variance {r['total_variance']:,.0f} "
              f"(volume {r['volume_variance']:,.0f}, price {r['price_variance']:,.0f})")
    if "sales_mix_and_volume_variance" in res:
        r = res["sales_mix_and_volume_variance"]
        for p in r["products"]:
            print(f"  {p['name']:16} mix variance {p['mix_variance']:>12,.0f}  quantity variance {p['quantity_variance']:>12,.0f}")
        print(f"Total: mix {r['total_sales_mix_variance']:,.0f}  quantity {r['total_sales_quantity_variance']:,.0f}")
    if "horizontal_analysis" in res:
        for name, r in res["horizontal_analysis"].items():
            pct = ["n/a" if p is None else f"{p:+.1%}" for p in r["pct_change"]]
            print(f"  {name:24} {r['values']}  →  {pct}")
    if "vertical_analysis" in res:
        for name, pcts in res["vertical_analysis"].items():
            print(f"  {name:24} {['%.1f%%' % (p*100) for p in pcts]}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fpa_planning(a):
    from .. import fpa_planning as F
    res = F.from_dict(_load_json(a.inputs))
    if "headcount_cost_schedule" in res:
        r = res["headcount_cost_schedule"]
        print(f"Headcount monthly cost: {['%.0f' % v for v in r['monthly_cost']]}  total {r['total_cost']:,.0f}")
    if "rolling_forecast" in res:
        r = res["rolling_forecast"]
        print(f"Rolling forecast: actuals {r['actuals_to_date']}  →  forecast {['%.1f' % v for v in r['forecast']]}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_breakeven(a):
    from .. import breakeven as B
    res = B.from_dict(_load_json(a.inputs))
    if "break_even_point" in res:
        r = res["break_even_point"]
        print(f"Break-even: {r['break_even_units']:,.0f} units ({r['break_even_revenue']:,.0f} revenue), contribution margin {r['contribution_margin_ratio']:.1%}")
    if "margin_of_safety" in res:
        r = res["margin_of_safety"]
        print(f"Margin of safety: {r['unit_cushion']:,.0f} units ({r['margin_of_safety_pct']:.1%})")
    if "degree_of_operating_leverage" in res:
        r = res["degree_of_operating_leverage"]
        print(f"Degree of operating leverage: {r['degree_of_operating_leverage']:.2f}x (operating profit {r['operating_profit']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_loss_reserving(a):
    from .. import loss_reserving as LR
    res = LR.from_dict(_load_json(a.inputs))
    if "chain_ladder" in res:
        r = res["chain_ladder"]
        print(f"Age-to-age factors: {['%.4f' % f for f in r['age_to_age_factors']]}")
        for ay in r["accident_years"]:
            print(f"  AY{ay['accident_year_index']}: latest {ay['latest_cumulative']:,.0f}  ultimate {ay['ultimate']:,.0f}  IBNR {ay['ibnr']:,.0f}")
        print(f"Total IBNR: {r['total_ibnr']:,.0f}  (total ultimate {r['total_ultimate']:,.0f})")
    if "bornhuetter_ferguson" in res:
        r = res["bornhuetter_ferguson"]
        for ay in r["accident_years"]:
            print(f"  AY{ay['accident_year_index']}: {ay['pct_reported']:.1%} reported  BF ultimate {ay['bf_ultimate']:,.0f}  (chain-ladder {ay['chain_ladder_ultimate']:,.0f})")
        print(f"Total BF ultimate: {r['total_bf_ultimate']:,.0f}  (BF IBNR {r['total_bf_ibnr']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_earnout_valuation(a):
    from .. import earnout_valuation as EO
    res = EO.from_dict(_load_json(a.inputs))
    if "scenario_weighted_earnout" in res:
        r = res["scenario_weighted_earnout"]
        print(f"Scenario-weighted earnout: expected payout {r['expected_payout']:,.0f}  PV {r['present_value']:,.0f}")
    if "binary_metric_earnout" in res:
        r = res["binary_metric_earnout"]
        print(f"Binary metric earnout: P(achieved) {r['risk_neutral_probability_achieved']:.1%}  PV {r['present_value']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_tax_provision(a):
    from .. import tax_provision as TP
    res = TP.from_dict(_load_json(a.inputs))
    if "deferred_tax_position" in res:
        r = res["deferred_tax_position"]
        print(f"Deferred tax: gross DTA {r['gross_dta']:,.0f}  gross DTL {r['gross_dtl']:,.0f}  net {r['net_deferred_tax']:,.0f}")
    if "valuation_allowance" in res:
        r = res["valuation_allowance"]
        print(f"Valuation allowance: {'required' if r['valuation_allowance_required'] else 'not required'} ({r['valuation_allowance']:,.0f}), net DTA {r['net_dta']:,.0f}")
    if "nol_carryforward_schedule" in res:
        r = res["nol_carryforward_schedule"]
        print(f"NOL schedule: total cash tax {r['total_cash_tax']:,.0f}  expired NOL {r['total_expired_nol']:,.0f}")
    if "effective_tax_rate_reconciliation" in res:
        r = res["effective_tax_rate_reconciliation"]
        print(f"Effective tax rate: {r['effective_tax_rate']:.1%} (statutory tax {r['statutory_tax']:,.0f}, total tax {r['total_tax']:,.0f})")
    if "deferred_tax_rollforward" in res:
        r = res["deferred_tax_rollforward"]
        print(f"Deferred tax rollforward: {r['beginning_balance']:,.0f} -> {r['ending_balance']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_real_estate_development(a):
    from .. import real_estate_development as RE
    res = RE.from_dict(_load_json(a.inputs))
    if "total_development_cost" in res:
        r = res["total_development_cost"]
        print(f"Total development cost: {r['total_development_cost']:,.0f} (contingency {r['contingency']:,.0f})")
    if "development_pro_forma" in res:
        r = res["development_pro_forma"]
        print(f"Development pro forma: cost basis {r['total_cost_basis']:,.0f}  exit value {r['exit_value']:,.0f}  "
              f"profit {r['development_profit']:,.0f}  yield on cost {r['yield_on_cost']:.2%}  "
              f"spread {r['development_spread_bps']:,.0f} bps  unlevered IRR {r['unlevered_irr_annual']:.1%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_working_capital_financing(a):
    from .. import working_capital_financing as WCF
    res = WCF.from_dict(_load_json(a.inputs))
    if "factoring_cost" in res:
        r = res["factoring_cost"]
        print(f"Factoring: advance {r['advance_amount']:,.0f}  fee {r['fee_amount']:,.0f}  net proceeds {r['net_proceeds']:,.0f}  effective APR {r['effective_annual_rate']:.1%}")
    if "early_payment_discount_apr" in res:
        print(f"Early-payment discount APR: {res['early_payment_discount_apr']:.1%}")
    if "asset_based_lending_availability" in res:
        r = res["asset_based_lending_availability"]
        print(f"ABL availability: borrowing base {r['borrowing_base']:,.0f}  available to draw {r['available_to_draw']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_retail_loans(a):
    from .. import retail_loans as RL
    res = RL.from_dict(_load_json(a.inputs))
    if "emi_calculation" in res:
        print(f"EMI: {res['emi_calculation']['emi']:,.2f}")
    if "amortization_schedule" in res:
        r = res["amortization_schedule"]
        print(f"Amortization: EMI {r['emi']:,.2f}  total interest {r['total_interest']:,.0f}  total payment {r['total_payment']:,.0f}")
    if "prepayment_impact" in res:
        r = res["prepayment_impact"]
        if r["loan_fully_repaid"]:
            print(f"Prepayment ({r['strategy']}): loan fully repaid, interest saved {r['interest_saved']:,.0f}")
        else:
            print(f"Prepayment ({r['strategy']}): new EMI {r['new_emi']:,.2f}  new tenure {r['new_tenure_months']} months  interest saved {r['interest_saved']:,.0f}")
    if "floating_rate_reset" in res:
        r = res["floating_rate_reset"]
        print(f"Rate reset ({r['strategy']}): {r['old_rate']:.2%} -> {r['new_rate']:.2%}  new EMI {r['new_emi']:,.2f}  new tenure {r['new_tenure_months']} months")
    if "foreclosure_payoff" in res:
        r = res["foreclosure_payoff"]
        print(f"Foreclosure payoff: {r['payoff_amount']:,.0f}  interest saved vs completing tenure {r['interest_saved_vs_completing_tenure']:,.0f}")
    if "loan_eligibility_foir" in res:
        r = res["loan_eligibility_foir"]
        print(f"Loan eligibility (FOIR): max eligible principal {r['max_eligible_principal']:,.0f} (available EMI capacity {r['available_emi_capacity']:,.0f})")
    if "step_up_emi_schedule" in res:
        r = res["step_up_emi_schedule"]
        print(f"Step-up EMI: base {r['base_emi']:,.2f} -> final {r['final_emi']:,.2f}  total interest {r['total_interest']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_retail_deposits(a):
    from .. import retail_deposits as RD
    res = RD.from_dict(_load_json(a.inputs))
    if "fixed_deposit_maturity" in res:
        r = res["fixed_deposit_maturity"]
        print(f"FD maturity: {r['maturity_value']:,.0f} (interest earned {r['interest_earned']:,.0f})")
    if "recurring_deposit_maturity" in res:
        r = res["recurring_deposit_maturity"]
        print(f"RD maturity: {r['maturity_value']:,.0f} (deposited {r['total_deposited']:,.0f}, interest earned {r['interest_earned']:,.0f})")
    if "recurring_deposit_premature_value" in res:
        r = res["recurring_deposit_premature_value"]
        print(f"RD premature closure value: {r['premature_value']:,.0f} (interest earned {r['interest_earned']:,.0f})")
    if "tds_on_interest" in res:
        r = res["tds_on_interest"]
        print(f"TDS: {'applicable' if r['tds_applicable'] else 'not applicable'} ({r['tds_amount']:,.0f}), net interest {r['net_interest']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_carry_trade(a):
    from .. import carry_trade as CT
    res = CT.from_dict(_load_json(a.inputs))
    if "covered_interest_rate_parity" in res:
        r = res["covered_interest_rate_parity"]
        print(f"CIP forward rate: {r['forward_rate']:,.4f}  (forward premium {r['forward_premium_pct']:.2%})")
    if "uncovered_carry_return" in res:
        r = res["uncovered_carry_return"]
        print(f"Uncovered carry return: {r['return_pct']:.2%}  (profit {r['profit']:,.0f})")
    if "break_even_depreciation" in res:
        r = res["break_even_depreciation"]
        print(f"Break-even depreciation: {r['break_even_depreciation_pct']:.2%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_revolving_credit(a):
    from .. import revolving_credit as RC
    res = RC.from_dict(_load_json(a.inputs))
    if "daily_balance_interest" in res:
        r = res["daily_balance_interest"]
        print(f"Daily-balance interest: {r['total_interest']:,.2f} over {r['num_days']} days (average balance {r['average_balance']:,.0f})")
    if "credit_card_minimum_payment_schedule" in res:
        r = res["credit_card_minimum_payment_schedule"]
        if r["paid_off"]:
            print(f"Minimum-payment schedule: paid off in {r['months_to_payoff']} months, total interest {r['total_interest_paid']:,.0f}")
        else:
            print(f"Minimum-payment schedule: NOT paid off within the simulated window (negative amortization or too slow); interest so far {r['total_interest_paid']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_npa_classification(a):
    from .. import npa_classification as NPA
    res = NPA.from_dict(_load_json(a.inputs))
    if "npa_provisioning" in res:
        r = res["npa_provisioning"]
        seg = f" ({r['segment']})" if "segment" in r else ""
        print(f"Classification: {r['classification']}{seg}  provision required {r['provision_required']:,.0f} ({r['provision_rate_effective']:.2%} of outstanding)")
    if "loan_book" in res:
        for r in res["loan_book"]:
            seg = f" [{r['segment']}]" if "segment" in r else ""
            print(f"  {r['classification']:12}{seg:28} outstanding {r['outstanding_amount']:>12,.0f}  provision {r['provision_required']:>12,.0f}")
        print(f"Total provision required: {res['total_provision_required']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))
