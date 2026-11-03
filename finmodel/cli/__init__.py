"""finmodel command-line interface (package; `finmodel.cli:main` and every old `finmodel.cli.cmd_*` name still resolve)."""
from __future__ import annotations

import argparse
import sys

from .. import __version__
from ._common import _dump, _load_json  # noqa: F401  (re-exported for old import paths)
from .cmds_valuation import (  # noqa: F401
    cmd_extract,
    cmd_catalog,
    cmd_three,
    cmd_dcf,
    cmd_projection,
    cmd_ratios,
    cmd_lbo,
    cmd_merger,
    cmd_transpile,
    cmd_comps,
    cmd_scores,
    cmd_costing,
    cmd_edgar,
    cmd_cycle,
    cmd_wacc,
    cmd_residual_income,
    cmd_sotp,
    cmd_startup,
    ts_table_summary,
    cmd_cap_table,
    cmd_vc_fund,
    cmd_percentage_of_completion,
    cmd_cash_flow_forecast,
    cmd_impact,
)
from .cmds_corporate import (  # noqa: F401
    cmd_strategy,
    cmd_ppa,
    cmd_impairment,
    cmd_audit_analytics,
    cmd_options,
    cmd_project_finance,
    cmd_dcf_diagnostics,
    cmd_portfolio,
    cmd_restructuring,
    cmd_bank_model,
    cmd_cohort_analysis,
    cmd_insurance_pricing,
    cmd_convertible_bonds,
    cmd_cmo,
    cmd_variance_analysis,
    cmd_fpa_planning,
    cmd_breakeven,
    cmd_loss_reserving,
    cmd_earnout_valuation,
    cmd_tax_provision,
    cmd_real_estate_development,
    cmd_working_capital_financing,
    cmd_retail_loans,
    cmd_retail_deposits,
    cmd_carry_trade,
    cmd_revolving_credit,
    cmd_npa_classification,
)
from .cmds_credit import (  # noqa: F401
    cmd_pipeline,
    cmd_credit_risk,
    cmd_interest_rate_risk,
    cmd_fixed_income_risk,
    cmd_credit_card_abs,
    cmd_sales_capacity_planning,
    cmd_lease_accounting,
    cmd_fx_hedging,
    cmd_stock_based_compensation,
    cmd_bond_amortization,
    cmd_foreign_currency_translation,
    cmd_inventory_costing,
    cmd_pension_accounting,
    cmd_nwc_peg,
    cmd_eps_calculation,
    cmd_investment_securities,
    cmd_consolidation,
    cmd_debt_covenants,
    cmd_asset_retirement_obligations,
    cmd_warranty_and_receivables_allowance,
)
from .cmds_india_tools import (  # noqa: F401
    cmd_investment_incentives,
    cmd_sector_investment_model,
    cmd_project_bankability,
    cmd_india_corporate_tax_regimes,
    cmd_india_depreciation_schedule,
    cmd_india_incentive_workbook,
    cmd_audit,
    cmd_charts,
    cmd_glossary,
    cmd_demo,
)


def main(argv=None):
    p = argparse.ArgumentParser(prog="finmodel", description="Financial modelling toolkit distilled from CFI templates")
    p.add_argument("--version", action="version", version=__version__)
    sp = p.add_subparsers(dest="cmd", required=True)

    x = sp.add_parser("extract", help="extract an Excel template into JSON+Markdown spec"); x.add_argument("files", nargs="+"); x.add_argument("-o", "--out", default="extracted"); x.set_defaults(fn=cmd_extract)
    c = sp.add_parser("catalog", help="build / list / verify / fetch public template sources / alternatives"); c.add_argument("action", choices=["build", "list", "verify", "fetch", "alternatives", "paid"]); c.add_argument("--title", help="paid: filter titles containing this text")
    c.add_argument("--source", nargs="*", help="damodaran asimplemodel exinfm cfi (cfi entries are catalogued only, never fetched)")
    c.add_argument("--dest", default="downloads"); c.add_argument("--overwrite", action="store_true"); c.add_argument("--limit", type=int); c.set_defaults(fn=cmd_catalog)
    t = sp.add_parser("three-statement", help="run the linked 3-statement model"); t.add_argument("inputs"); t.add_argument("--xlsx"); t.add_argument("--json-out"); t.add_argument("--table", help="income_statement|balance_sheet|cash_flow|schedules|all"); t.set_defaults(fn=cmd_three)
    d = sp.add_parser("dcf", help="run the unlevered DCF"); d.add_argument("inputs"); d.add_argument("--xlsx"); d.add_argument("--json-out"); d.add_argument("--sensitivity", action="store_true"); d.set_defaults(fn=cmd_dcf)
    j = sp.add_parser("projection", help="run the bottom-up projection"); j.add_argument("inputs"); j.add_argument("--xlsx"); j.add_argument("--json-out"); j.set_defaults(fn=cmd_projection)
    r = sp.add_parser("ratios", help="ratio analysis from {is:{}, bs:{}}"); r.add_argument("inputs"); r.add_argument("--json-out"); r.set_defaults(fn=cmd_ratios)
    l = sp.add_parser("lbo", help="run the LBO model"); l.add_argument("inputs"); l.add_argument("--xlsx"); l.add_argument("--json-out"); l.set_defaults(fn=cmd_lbo)
    g = sp.add_parser("merger", help="run the merger (accretion/dilution) model"); g.add_argument("inputs"); g.add_argument("--xlsx"); g.add_argument("--json-out"); g.set_defaults(fn=cmd_merger)
    tp = sp.add_parser("transpile", help="convert a workbook's formulas to Python and verify against cached values"); tp.add_argument("files", nargs="+"); tp.add_argument("-o", "--out"); tp.add_argument("--show", type=int, default=5); tp.set_defaults(fn=cmd_transpile)
    cp = sp.add_parser("comps", help="trading comps, precedent transactions, implied valuation and football field"); cp.add_argument("inputs"); cp.add_argument("--xlsx"); cp.add_argument("--json-out"); cp.set_defaults(fn=cmd_comps)
    sc = sp.add_parser("scores", help="Altman Z, Piotroski F, Beneish M from two fiscal years of statement data"); sc.add_argument("inputs"); sc.add_argument("--json-out"); sc.set_defaults(fn=cmd_scores)
    co = sp.add_parser("costing", help="EUA-style resource allocation, cost allocation and income diversification"); co.add_argument("inputs"); co.add_argument("--json-out"); co.set_defaults(fn=cmd_costing)
    ed = sp.add_parser("edgar", help="pull annual statements for a CIK from SEC EDGAR company facts"); ed.add_argument("cik"); ed.add_argument("--user-agent", required=True, help="e.g. 'my-tool name@example.com' (SEC requires a contact)"); ed.add_argument("--years", type=int, default=8); ed.add_argument("--cache-dir"); ed.add_argument("--json-out"); ed.set_defaults(fn=cmd_edgar)
    cy = sp.add_parser("cycle", help="where a company's LTM year sits in its own margin cycle, and data-driven DCF scenario targets from its own history"); cy.add_argument("edgar_json", help="a data/edgar/<TICKER>.json extract (finmodel edgar --json-out)"); cy.add_argument("--sector", default="default", choices=["steel", "oil_gas", "software", "banking", "reit", "airline", "insurance", "semiconductor", "utility", "pharma", "default"]); cy.add_argument("--field", help="numerator field, e.g. net_income for banks (default: operating_income)"); cy.add_argument("--revenue-field", dest="revenue_field", default="revenue", help="denominator field, e.g. equity for banks' ROE (default: revenue)"); cy.add_argument("--periods", type=int, default=8); cy.add_argument("--as-of"); cy.add_argument("--json-out"); cy.set_defaults(fn=cmd_cycle)
    wc = sp.add_parser("wacc", help="CAPM cost of equity, synthetic-rating cost of debt, bottom-up beta and WACC"); wc.add_argument("inputs"); wc.add_argument("--json-out"); wc.set_defaults(fn=cmd_wacc)
    ri = sp.add_parser("residual-income", help="residual-income (EBO) equity valuation and/or EVA firm valuation"); ri.add_argument("inputs"); ri.add_argument("--json-out"); ri.set_defaults(fn=cmd_residual_income)
    so = sp.add_parser("sotp", help="sum-of-the-parts valuation across segments"); so.add_argument("inputs"); so.add_argument("--json-out"); so.set_defaults(fn=cmd_sotp)
    from .. import startup_model as _SM
    su = sp.add_parser("startup", help="new-business 3-statement projection + DCF valuation, benchmarked against real sector peer data"); su.add_argument("inputs"); su.add_argument("--benchmark-sector", choices=list(_SM.SECTOR_PEER_TICKERS)); su.add_argument("--json-out"); su.set_defaults(fn=cmd_startup)
    ct = sp.add_parser("cap-table", help="priced-round dilution (with the option-pool shuffle) and an exit liquidation-preference waterfall"); ct.add_argument("inputs"); ct.add_argument("--json-out"); ct.set_defaults(fn=cmd_cap_table)
    vf = sp.add_parser("vc-fund", help="VC/PE fund LP metrics (DPI/RVPI/TVPI/IRR), deal-level MOIC/IRR, and European or American (deal-by-deal, with clawback) carry waterfalls"); vf.add_argument("inputs"); vf.add_argument("--json-out"); vf.set_defaults(fn=cmd_vc_fund)
    cf = sp.add_parser("cash-flow-forecast", help="13-week rolling direct-method cash flow forecast, covenant-breach flagging, forecast-vs-actual variance"); cf.add_argument("inputs"); cf.add_argument("--json-out"); cf.set_defaults(fn=cmd_cash_flow_forecast)
    ic = sp.add_parser("impact", help="2X Criteria gender-lens screen, Impact Management Project ABC classification, GHG intensity"); ic.add_argument("inputs"); ic.add_argument("--json-out"); ic.set_defaults(fn=cmd_impact)
    sf = sp.add_parser("strategy", help="TAM/SAM/SOM market sizing, BCG growth-share matrix, GE-McKinsey nine-box matrix"); sf.add_argument("inputs"); sf.add_argument("--json-out"); sf.set_defaults(fn=cmd_strategy)
    ppa = sp.add_parser("ppa", help="purchase price allocation: relief-from-royalty, MPEEM, cost approach, ASC 805 goodwill residual"); ppa.add_argument("inputs"); ppa.add_argument("--json-out"); ppa.set_defaults(fn=cmd_ppa)
    imp = sp.add_parser("impairment", help="ASC 350 goodwill / ASC 350-30 indefinite-lived intangible / ASC 360 long-lived-asset impairment tests"); imp.add_argument("inputs"); imp.add_argument("--json-out"); imp.set_defaults(fn=cmd_impairment)
    aa = sp.add_parser("audit-analytics", help="Benford's Law digit-conformity test and rule-based journal-entry testing (JET)"); aa.add_argument("inputs"); aa.add_argument("--json-out"); aa.set_defaults(fn=cmd_audit_analytics)
    opt = sp.add_parser("options", help="Black-Scholes option pricing, the Greeks, put-call parity, implied volatility"); opt.add_argument("inputs"); opt.add_argument("--json-out"); opt.set_defaults(fn=cmd_options)
    pf = sp.add_parser("project-finance", help="DSCR-based debt sizing/sculpting, LLCR, cap rate/NOI real-estate valuation"); pf.add_argument("inputs"); pf.add_argument("--json-out"); pf.set_defaults(fn=cmd_project_finance)
    pfo = sp.add_parser("portfolio", help="Markowitz efficient frontier, global minimum-variance and tangency portfolios, Capital Allocation Line"); pfo.add_argument("inputs"); pfo.add_argument("--json-out"); pfo.set_defaults(fn=cmd_portfolio)
    rs = sp.add_parser("restructuring", help="absolute-priority recovery waterfall, fulcrum security, DIP financing sizing, post-emergence capital structure"); rs.add_argument("inputs"); rs.add_argument("--json-out"); rs.set_defaults(fn=cmd_restructuring)
    bm = sp.add_parser("bank-model", help="bank operating model: NII/NIM, provision for credit losses, efficiency ratio, regulatory capital ratios"); bm.add_argument("inputs"); bm.add_argument("--json-out"); bm.set_defaults(fn=cmd_bank_model)
    ca = sp.add_parser("cohort", help="SaaS cohort retention curves, GRR/NRR, LTV, LTV:CAC, CAC payback"); ca.add_argument("inputs"); ca.add_argument("--json-out"); ca.set_defaults(fn=cmd_cohort_analysis)
    ip = sp.add_parser("insurance-pricing", help="loss/expense/combined/operating ratios, loss-cost-multiplier rate making"); ip.add_argument("inputs"); ip.add_argument("--json-out"); ip.set_defaults(fn=cmd_insurance_pricing)
    cvb = sp.add_parser("convertible", help="convertible bond bond-floor + embedded-option (two-component) valuation, conversion premium"); cvb.add_argument("inputs"); cvb.add_argument("--json-out"); cvb.set_defaults(fn=cmd_convertible_bonds)
    cmo = sp.add_parser("cmo", help="CMO: PSA prepayment modeling, sequential-pay tranching, weighted average life"); cmo.add_argument("inputs"); cmo.add_argument("--json-out"); cmo.set_defaults(fn=cmd_cmo)
    dcfd = sp.add_parser("dcf-diagnostics", help="flags a DCF that double-counts the interest tax shield (levered cash taxes in an unlevered FCF)"); dcfd.add_argument("inputs"); dcfd.add_argument("--json-out"); dcfd.set_defaults(fn=cmd_dcf_diagnostics)
    va = sp.add_parser("variance-analysis", help="budget-vs-actual volume/price/mix variance, horizontal and vertical (common-size) analysis"); va.add_argument("inputs"); va.add_argument("--json-out"); va.set_defaults(fn=cmd_variance_analysis)
    fpap = sp.add_parser("fpa-planning", help="headcount/workforce cost schedule, driver-based rolling forecast"); fpap.add_argument("inputs"); fpap.add_argument("--json-out"); fpap.set_defaults(fn=cmd_fpa_planning)
    bke = sp.add_parser("breakeven", help="break-even point, margin of safety, degree of operating leverage (CVP analysis)"); bke.add_argument("inputs"); bke.add_argument("--json-out"); bke.set_defaults(fn=cmd_breakeven)
    lr = sp.add_parser("loss-reserving", help="chain-ladder loss development triangle (age-to-age factors, projected ultimates, IBNR) and Bornhuetter-Ferguson"); lr.add_argument("inputs"); lr.add_argument("--json-out"); lr.set_defaults(fn=cmd_loss_reserving)
    eov = sp.add_parser("earnout-valuation", help="M&A contingent-consideration fair value: scenario-weighted expected payout, or a binary metric-threshold digital option"); eov.add_argument("inputs"); eov.add_argument("--json-out"); eov.set_defaults(fn=cmd_earnout_valuation)
    poc = sp.add_parser("percentage-of-completion", help="cost-to-cost revenue recognition for long-term contracts: percent complete, revenue/gross profit to date, over/under-billing"); poc.add_argument("inputs"); poc.add_argument("--json-out"); poc.set_defaults(fn=cmd_percentage_of_completion)
    cca = sp.add_parser("credit-card-abs", help="credit-card master-trust securitization: excess spread, the 3-month early-amortization trigger, revolving/amortization cash flows"); cca.add_argument("inputs"); cca.add_argument("--json-out"); cca.set_defaults(fn=cmd_credit_card_abs)
    scp = sp.add_parser("sales-capacity-planning", help="rep productivity ramp curves, bookings-capacity forecasting, reps needed to hit a target"); scp.add_argument("inputs"); scp.add_argument("--json-out"); scp.set_defaults(fn=cmd_sales_capacity_planning)
    lac = sp.add_parser("lease-accounting", help="ASC 842 lease classification, initial measurement, and finance/operating lease expense schedules"); lac.add_argument("inputs"); lac.add_argument("--json-out"); lac.set_defaults(fn=cmd_lease_accounting)
    fxh = sp.add_parser("fx-hedging", help="corporate FX exposure hedging: forward hedge vs money-market hedge vs unhedged"); fxh.add_argument("inputs"); fxh.add_argument("--json-out"); fxh.set_defaults(fn=cmd_fx_hedging)
    sbc = sp.add_parser("stock-based-compensation", help="ASC 718 RSU/option grant fair value and straight-line vs graded-vesting expense attribution"); sbc.add_argument("inputs"); sbc.add_argument("--json-out"); sbc.set_defaults(fn=cmd_stock_based_compensation)
    bam = sp.add_parser("bond-amortization", help="effective-interest bond premium/discount amortization schedule"); bam.add_argument("inputs"); bam.add_argument("--json-out"); bam.set_defaults(fn=cmd_bond_amortization)
    fct = sp.add_parser("fx-translation", help="ASC 830 current-rate method: translate a foreign subsidiary's statements, with the Cumulative Translation Adjustment plug"); fct.add_argument("inputs"); fct.add_argument("--json-out"); fct.set_defaults(fn=cmd_foreign_currency_translation)
    ivc = sp.add_parser("inventory-costing", help="FIFO, LIFO, and weighted-average cost-flow assumptions for cost of goods sold and ending inventory"); ivc.add_argument("inputs"); ivc.add_argument("--json-out"); ivc.set_defaults(fn=cmd_inventory_costing)
    pea = sp.add_parser("pension-accounting", help="ASC 715 PBO/plan-asset roll-forwards, funded status, and net periodic pension cost"); pea.add_argument("inputs"); pea.add_argument("--json-out"); pea.set_defaults(fn=cmd_pension_accounting)
    nwc = sp.add_parser("nwc-peg", help="M&A net-working-capital peg and closing true-up purchase-price adjustment"); nwc.add_argument("inputs"); nwc.add_argument("--json-out"); nwc.set_defaults(fn=cmd_nwc_peg)
    epsc = sp.add_parser("eps", help="ASC 260 basic and diluted EPS (treasury stock method, if-converted method, antidilution test)"); epsc.add_argument("inputs"); epsc.add_argument("--json-out"); epsc.set_defaults(fn=cmd_eps_calculation)
    invs = sp.add_parser("investment-securities", help="ASC 320 trading/AFS/HTM classification and unrealized gain/loss routing, OCI reclassification on sale"); invs.add_argument("inputs"); invs.add_argument("--json-out"); invs.set_defaults(fn=cmd_investment_securities)
    cons = sp.add_parser("consolidation", help="ASC 810 consolidated net income, noncontrolling interest (NCI) carve-out, NCI at acquisition"); cons.add_argument("inputs"); cons.add_argument("--json-out"); cons.set_defaults(fn=cmd_consolidation)
    dcv = sp.add_parser("debt-covenants", help="borrower-side leverage/interest-coverage/fixed-charge-coverage covenant compliance testing"); dcv.add_argument("inputs"); dcv.add_argument("--json-out"); dcv.set_defaults(fn=cmd_debt_covenants)
    aro = sp.add_parser("aro", help="ASC 410 asset retirement obligation: initial PV recognition, accretion schedule, settlement gain/loss"); aro.add_argument("inputs"); aro.add_argument("--json-out"); aro.set_defaults(fn=cmd_asset_retirement_obligations)
    wra = sp.add_parser("warranty-receivables", help="warranty reserve roll-forward (expected-cost method) and CECL aging-method receivables allowance"); wra.add_argument("inputs"); wra.add_argument("--json-out"); wra.set_defaults(fn=cmd_warranty_and_receivables_allowance)
    ii = sp.add_parser("investment-incentives", help="capital/interest/net-tax/employment investment-incentive mechanics used by Indian central and state schemes (PLI, BIPA-style state schemes, etc.)"); ii.add_argument("inputs"); ii.add_argument("--json-out"); ii.set_defaults(fn=cmd_investment_incentives)
    sim = sp.add_parser("sector-investment-model", help="sample state/sector investment model: land cost + capex stack netted against a discounted central+state incentive package"); sim.add_argument("inputs"); sim.add_argument("--json-out"); sim.set_defaults(fn=cmd_sector_investment_model)
    pbk = sp.add_parser("project-bankability", help="IRR/ROI/payback with and without incentives, plus a state/sector ranking that flags projects incentives make bankable"); pbk.add_argument("inputs"); pbk.add_argument("--json-out"); pbk.set_defaults(fn=cmd_project_bankability)
    iiw = sp.add_parser("india-incentive-workbook", help="write the consolidated India state/central incentive + land-cost + 28-state matrix Excel workbook"); iiw.add_argument("output", help="output .xlsx path"); iiw.set_defaults(fn=cmd_india_incentive_workbook)
    tax = sp.add_parser("india-tax-regimes", help="Section 115BAB vs 115BAA vs standard-regime post-tax IRR comparison, and the CGTMSE guarantee fee's effect on DSCR"); tax.add_argument("inputs"); tax.add_argument("--json-out"); tax.set_defaults(fn=cmd_india_corporate_tax_regimes)
    dep = sp.add_parser("india-depreciation-schedule", help="Income Tax Act WDV block-of-assets depreciation, section 50 short-term capital gain on block extinguishment, section 32(1)(iia) additional depreciation"); dep.add_argument("inputs"); dep.add_argument("--json-out"); dep.set_defaults(fn=cmd_india_depreciation_schedule)
    txp = sp.add_parser("tax-provision", help="deferred tax position, valuation allowance, NOL carryforward (pre-2018/post-2017 baskets), effective-rate reconciliation"); txp.add_argument("inputs"); txp.add_argument("--json-out"); txp.set_defaults(fn=cmd_tax_provision)
    red = sp.add_parser("real-estate-development", help="ground-up development pro forma: TDC, construction-loan draw schedule, yield on cost, development spread, unlevered IRR"); red.add_argument("inputs"); red.add_argument("--json-out"); red.set_defaults(fn=cmd_real_estate_development)
    wcf = sp.add_parser("working-capital-financing", help="invoice factoring cost, early-payment-discount APR, asset-based-lending borrowing-base availability"); wcf.add_argument("inputs"); wcf.add_argument("--json-out"); wcf.set_defaults(fn=cmd_working_capital_financing)
    rl = sp.add_parser("retail-loans", help="EMI, amortization schedule, prepayment (reduce-tenure/reduce-EMI), floating-rate reset, foreclosure payoff, FOIR loan eligibility, step-up EMI"); rl.add_argument("inputs"); rl.add_argument("--json-out"); rl.set_defaults(fn=cmd_retail_loans)
    rdp = sp.add_parser("retail-deposits", help="fixed deposit maturity, recurring deposit maturity (per-installment compounding), premature RD closure, Section 194A TDS"); rdp.add_argument("inputs"); rdp.add_argument("--json-out"); rdp.set_defaults(fn=cmd_retail_deposits)
    ctd = sp.add_parser("carry-trade", help="covered interest rate parity forward rate, unhedged FX carry return, break-even depreciation"); ctd.add_argument("inputs"); ctd.add_argument("--json-out"); ctd.set_defaults(fn=cmd_carry_trade)
    rvc = sp.add_parser("revolving-credit", help="cash-credit/overdraft and credit-card daily-balance interest; the minimum-payment trap"); rvc.add_argument("inputs"); rvc.add_argument("--json-out"); rvc.set_defaults(fn=cmd_revolving_credit)
    npa = sp.add_parser("npa-classification", help="RBI IRAC asset classification (Standard/SMA/NPA buckets) and secured/unsecured provisioning"); npa.add_argument("inputs"); npa.add_argument("--json-out"); npa.set_defaults(fn=cmd_npa_classification)
    pln = sp.add_parser("pipeline", help="chain multiple finmodel modules together, referencing earlier steps' outputs with ${step.path} placeholders"); pln.add_argument("inputs"); pln.add_argument("--json-out"); pln.set_defaults(fn=cmd_pipeline)
    crk = sp.add_parser("credit-risk", help="expected loss (PD x LGD x EAD) and the Basel IRB risk-weighted-assets formula"); crk.add_argument("inputs"); crk.add_argument("--json-out"); crk.set_defaults(fn=cmd_credit_risk)
    irr = sp.add_parser("interest-rate-risk", help="bank repricing gap and first-order NII sensitivity to a rate shock"); irr.add_argument("inputs"); irr.add_argument("--json-out"); irr.set_defaults(fn=cmd_interest_rate_risk)
    fir = sp.add_parser("fixed-income-risk", help="bond price, Macaulay/modified duration, DV01, convexity"); fir.add_argument("inputs"); fir.add_argument("--json-out"); fir.set_defaults(fn=cmd_fixed_income_risk)
    au = sp.add_parser("audit", help="workbook audit: error values, hard-coded plugs, inconsistent formulas, links, hidden sheets"); au.add_argument("file"); au.add_argument("--recompute", action="store_true", help="also verify every formula against its cached value (finmodel.xlcalc)"); au.add_argument("--show", type=int, default=20); au.add_argument("--json-out"); au.add_argument("--markdown-out"); au.set_defaults(fn=cmd_audit)
    ch = sp.add_parser("charts", help="render the chart template for an engine's inputs to a self-contained HTML report"); ch.add_argument("engine", choices=["three_statement", "dcf", "lbo", "merger", "projection", "comps"]); ch.add_argument("inputs"); ch.add_argument("-o", "--out", default="out/charts.html"); ch.add_argument("--title"); ch.set_defaults(fn=cmd_charts)
    gl = sp.add_parser("glossary", help="look up a financial term (definition, formula, GAAP vs IFRS note)"); gl.add_argument("query", nargs="+"); gl.add_argument("--deep", action="store_true"); gl.add_argument("--limit", type=int, default=5); gl.set_defaults(fn=cmd_glossary)
    m = sp.add_parser("demo", help="run all engines on the bundled examples and write workbooks"); m.add_argument("--out", default="out"); m.set_defaults(fn=cmd_demo)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
