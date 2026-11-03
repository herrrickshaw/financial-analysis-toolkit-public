"""Credit, banking, fixed-income and accounting-standard commands."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import _load_json


def cmd_pipeline(a):
    from .. import pipeline as PL
    res = PL.from_dict(_load_json(a.inputs))
    for name in res["order"]:
        print(f"Step '{name}': {', '.join(res['steps'][name].keys())}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_credit_risk(a):
    from .. import credit_risk as CR
    res = CR.from_dict(_load_json(a.inputs))
    if "expected_loss" in res:
        r = res["expected_loss"]
        print(f"Expected loss: {r['expected_loss']:,.2f} (PD {r['pd']:.2%} x LGD {r['lgd']:.2%} x EAD {r['ead']:,.0f})")
    if "basel_irb_corporate" in res:
        r = res["basel_irb_corporate"]
        print(f"Basel IRB: risk weight {r['risk_weight_pct']:.1%}  RWA {r['risk_weighted_assets']:,.0f}  min capital {r['minimum_capital_required']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_interest_rate_risk(a):
    from .. import interest_rate_risk as IRR
    res = IRR.from_dict(_load_json(a.inputs))
    if "repricing_gap" in res:
        r = res["repricing_gap"]
        for b in r["buckets"]:
            print(f"  {b['name']:10} gap {b['gap']:>14,.0f}  cumulative {b['cumulative_gap']:>14,.0f}")
        print(f"Total gap: {r['total_gap']:,.0f}  (gap ratio {r['gap_ratio']:.1%})")
    if "nii_sensitivity" in res:
        r = res["nii_sensitivity"]
        print(f"NII sensitivity to {r['rate_shock']:+.2%} rate shock: {r['delta_nii']:+,.0f} ({'asset' if r['nii_rises_with_rates'] else 'liability'}-sensitive)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fixed_income_risk(a):
    from .. import fixed_income_risk as FIR
    res = FIR.from_dict(_load_json(a.inputs))
    if "bond_price_and_duration" in res:
        r = res["bond_price_and_duration"]
        print(f"Bond: price {r['price']:,.4f}  Macaulay duration {r['macaulay_duration_years']:.4f}y  "
              f"modified duration {r['modified_duration']:.4f}  DV01 {r['dv01']:.4f}  convexity {r['convexity']:.4f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_credit_card_abs(a):
    from .. import credit_card_abs as CCA
    res = CCA.from_dict(_load_json(a.inputs))
    if "excess_spread" in res:
        print(f"Excess spread: {res['excess_spread']['value']:.2%}")
    if "early_amortization_trigger" in res:
        r = res["early_amortization_trigger"]
        status = f"triggered at month {r['triggered_month']}" if r["triggered"] else "not triggered"
        print(f"Early amortization: {status}")
    if "master_trust_cash_flows" in res:
        r = res["master_trust_cash_flows"]
        print(f"Master trust: {r['months_to_full_paydown']} months to full paydown "
              f"({r['revolving_period_months']} revolving, fully paid down: {r['fully_paid_down']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_sales_capacity_planning(a):
    from .. import sales_capacity_planning as SCP
    res = SCP.from_dict(_load_json(a.inputs))
    if "sales_capacity_schedule" in res:
        r = res["sales_capacity_schedule"]
        for p in r["periods"]:
            print(f"  Period {p['period']}: headcount {p['headcount']:.1f}  bookings capacity {p['bookings_capacity']:,.0f}")
        print(f"Total capacity: {r['total_capacity']:,.0f}")
    if "reps_needed_for_target" in res:
        r = res["reps_needed_for_target"]
        print(f"Reps needed: {r['reps_needed']:.1f} (effective quota {r['effective_quota_per_rep']:,.0f} at {r['ramp_fraction_at_target_period']:.0%} ramp)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_lease_accounting(a):
    from .. import lease_accounting as LA
    res = LA.from_dict(_load_json(a.inputs))
    if "classify_lease" in res:
        r = res["classify_lease"]
        print(f"Lease classification: {r['classification']}" + (f" ({'; '.join(r['reasons'])})" if r["reasons"] else ""))
    if "initial_measurement" in res:
        r = res["initial_measurement"]
        print(f"Initial measurement: lease liability {r['lease_liability']:,.0f}  ROU asset {r['rou_asset']:,.0f}")
    if "finance_lease_schedule" in res:
        r = res["finance_lease_schedule"]
        print(f"Finance lease: period 1 expense {r['schedule'][0]['total_expense']:,.0f} -> "
              f"period {len(r['schedule'])} expense {r['schedule'][-1]['total_expense']:,.0f} (front-loaded)")
    if "operating_lease_schedule" in res:
        r = res["operating_lease_schedule"]
        print(f"Operating lease: flat expense {r['straight_line_expense']:,.0f} every period")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fx_hedging(a):
    from .. import fx_hedging as FXH
    res = FXH.from_dict(_load_json(a.inputs))
    if "fx_hedge_comparison" in res:
        r = res["fx_hedge_comparison"]
        line = f"Forward hedge {r['forward_hedge_value']:,.0f}  Money-market hedge {r['money_market_hedge_value']:,.0f}"
        if "unhedged_value" in r:
            line += f"  Unhedged {r['unhedged_value']:,.0f}"
        print(line)
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_stock_based_compensation(a):
    from .. import stock_based_compensation as SBC
    res = SBC.from_dict(_load_json(a.inputs))
    if "rsu_grant_fair_value" in res:
        print(f"RSU grant fair value: {res['rsu_grant_fair_value']['value']:,.0f}")
    if "stock_option_grant_fair_value" in res:
        r = res["stock_option_grant_fair_value"]
        print(f"Option grant fair value: {r['total_fair_value']:,.0f}  ({r['fair_value_per_share']:.4f} per share)")
    if "straight_line_expense_schedule" in res:
        r = res["straight_line_expense_schedule"]
        print(f"Straight-line expense: {r['period_expense']:,.0f} per period over {len(r['schedule'])} periods")
    if "graded_vesting_expense_schedule" in res:
        r = res["graded_vesting_expense_schedule"]
        print(f"Graded vesting: period 1 expense {r['schedule'][0]['expense']:,.0f} -> "
              f"period {len(r['schedule'])} expense {r['schedule'][-1]['expense']:,.0f} (front-loaded)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_bond_amortization(a):
    from .. import bond_amortization as BA
    res = BA.from_dict(_load_json(a.inputs))
    if "bond_amortization_schedule" in res:
        r = res["bond_amortization_schedule"]
        print(f"Bond issued at {r['issued_at']}: issue price {r['issue_price']:,.2f}  "
              f"(premium/discount {r['premium_or_discount']:,.2f})  ending carrying value {r['schedule'][-1]['carrying_value']:,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_foreign_currency_translation(a):
    from .. import foreign_currency_translation as FCT
    res = FCT.from_dict(_load_json(a.inputs))
    if "current_rate_translation" in res:
        r = res["current_rate_translation"]
        print(f"Translated net income: {r['translated_net_income']:,.2f}")
        print(f"Translated assets {r['translated_assets']:,.2f} = liabilities {r['translated_liabilities']:,.2f} + "
              f"equity {r['total_translated_equity']:,.2f}  (CTA {r['cumulative_translation_adjustment']:+,.2f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_inventory_costing(a):
    from .. import inventory_costing as IC
    res = IC.from_dict(_load_json(a.inputs))
    for method in ("fifo", "lifo", "weighted_average"):
        if method in res:
            r = res[method]
            print(f"{method}: COGS {r['cogs']:,.2f}  ending inventory {r['ending_inventory_value']:,.2f}")
    if "compare_costing_methods" in res:
        r = res["compare_costing_methods"]
        print(f"Total cost available: {r['total_cost_available']:,.2f}")
        for method in ("fifo", "weighted_average", "lifo"):
            print(f"  {method:16} COGS {r[method]['cogs']:>12,.2f}  ending inventory {r[method]['ending_inventory_value']:>12,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_pension_accounting(a):
    from .. import pension_accounting as PA
    res = PA.from_dict(_load_json(a.inputs))
    if "pbo_rollforward" in res:
        r = res["pbo_rollforward"]
        print(f"PBO: {r['beginning_pbo']:,.0f} -> {r['ending_pbo']:,.0f}")
    if "plan_assets_rollforward" in res:
        r = res["plan_assets_rollforward"]
        print(f"Plan assets: {r['beginning_plan_assets']:,.0f} -> {r['ending_plan_assets']:,.0f}")
    if "funded_status" in res:
        r = res["funded_status"]
        print(f"Funded status: {r['funded_status']:+,.0f} ({r['classification']})")
    if "net_periodic_pension_cost" in res:
        r = res["net_periodic_pension_cost"]
        print(f"Net periodic pension cost: {r['net_periodic_pension_cost']:,.0f}")
    if "asset_gain_loss" in res:
        print(f"Asset gain/loss: {res['asset_gain_loss']['value']:+,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_nwc_peg(a):
    from .. import nwc_peg as NWC
    res = NWC.from_dict(_load_json(a.inputs))
    for key in ("nwc_true_up", "working_capital_adjustment"):
        if key in res:
            r = res[key]
            print(f"NWC true-up: actual {r['actual_nwc_at_closing']:,.0f} vs peg {r['peg_nwc']:,.0f}  "
                  f"adjustment {r['purchase_price_adjustment']:+,.0f} ({r['direction']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_eps_calculation(a):
    from .. import eps_calculation as EPSC
    res = EPSC.from_dict(_load_json(a.inputs))
    if "basic_eps" in res:
        print(f"Basic EPS: {res['basic_eps']['basic_eps']:.4f}")
    if "diluted_eps" in res:
        r = res["diluted_eps"]
        print(f"Diluted EPS: {r['diluted_eps']:.4f}  (basic {r['basic_eps']:.4f}, "
              f"{len(r['dilutive_securities_included'])} dilutive securities included)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_investment_securities(a):
    from .. import investment_securities as IS
    res = IS.from_dict(_load_json(a.inputs))
    if "classify_and_measure" in res:
        r = res["classify_and_measure"]
        print(f"{r['classification']}: carrying value {r['carrying_value']:,.0f}  "
              f"(income statement impact {r['income_statement_impact']:+,.0f}, OCI impact {r['oci_impact']:+,.0f})")
    if "realized_gain_loss_on_sale" in res:
        r = res["realized_gain_loss_on_sale"]
        print(f"Realized gain/loss: {r['realized_gain_loss']:+,.0f}  (reclassified from OCI {r['reclassification_adjustment_from_oci']:+,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_consolidation(a):
    from .. import consolidation as CONS
    res = CONS.from_dict(_load_json(a.inputs))
    if "consolidated_net_income" in res:
        r = res["consolidated_net_income"]
        print(f"Consolidated NI: {r['consolidated_net_income']:,.0f}  NCI share {r['nci_share_of_net_income']:,.0f}  "
              f"attributable to parent {r['net_income_attributable_to_parent']:,.0f}")
    if "nci_balance_sheet" in res:
        r = res["nci_balance_sheet"]
        print(f"NCI balance: {r['nci_balance']:,.0f}  (parent share {r['parent_share_of_subsidiary_equity']:,.0f})")
    if "nci_at_acquisition_fair_value_method" in res:
        print(f"NCI at acquisition (fair value method): {res['nci_at_acquisition_fair_value_method']['nci_initial_value']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_debt_covenants(a):
    from .. import debt_covenants as DC
    res = DC.from_dict(_load_json(a.inputs))
    for key in ("leverage_ratio_covenant", "interest_coverage_covenant", "fixed_charge_coverage_covenant"):
        if key in res:
            r = res[key]
            status = "OK" if r["compliant"] else "*** BREACH ***"
            print(f"  {r['covenant']:28} headroom {r['headroom']:+.3f}  {status}")
    if "covenant_compliance_summary" in res:
        s = res["covenant_compliance_summary"]
        print(f"Covenant summary: {s['total_covenants_tested']} tested, all compliant: {s['all_compliant']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_asset_retirement_obligations(a):
    from .. import asset_retirement_obligations as ARO
    res = ARO.from_dict(_load_json(a.inputs))
    if "initial_aro_recognition" in res:
        r = res["initial_aro_recognition"]
        print(f"Initial ARO liability: {r['initial_aro_liability']:,.2f}")
    if "accretion_schedule" in res:
        r = res["accretion_schedule"]
        print(f"Accretion schedule: {len(r['schedule'])} years  final ARO liability {r['final_aro_liability']:,.2f}")
    if "settlement_gain_loss" in res:
        r = res["settlement_gain_loss"]
        print(f"Settlement: {r['gain_loss']:+,.2f} ({r['classification']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_warranty_and_receivables_allowance(a):
    from .. import warranty_and_receivables_allowance as WRA
    res = WRA.from_dict(_load_json(a.inputs))
    if "warranty_reserve_rollforward" in res:
        r = res["warranty_reserve_rollforward"]
        print(f"Warranty reserve: {r['beginning_reserve']:,.0f} -> {r['ending_reserve']:,.0f}  (additions {r['additions']:,.0f})")
    if "receivables_allowance_aging_method" in res:
        r = res["receivables_allowance_aging_method"]
        for b in r["buckets"]:
            print(f"  {b['bucket']:10} balance {b['balance']:>12,.0f}  allowance {b['allowance']:>10,.0f}")
        print(f"Total allowance: {r['total_allowance']:,.0f}  (net realizable {r['net_realizable_receivables']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))
