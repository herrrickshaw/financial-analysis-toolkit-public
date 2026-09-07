"""finmodel: financial modelling toolkit distilled from CFI Excel templates.

Engines
-------
- three_statement : linked IS / BS / CF with working-capital, PP&E and debt schedules
- dcf             : unlevered FCF DCF with perpetuity + exit-multiple terminal value, XNPV / XIRR
- projection      : bottom-up projection (sales by product, payroll, opex) -> 3 statements -> ratios
- ratios          : profitability / efficiency / liquidity / leverage / coverage ratios

Utilities
---------
- fin      : Excel-compatible finance maths (YEARFRAC, XNPV, XIRR, NPV, IRR, NETWORKDAYS, PMT)
- extract  : turn any .xlsx/.xls template into a JSON + Markdown spec (labels, inputs, formulas, links)
- catalog  : catalog / verify / fetch template sources (CFI dashboard, Damodaran, ASimpleModel, exinfm)
- excel    : write engine outputs to .xlsx with live formulas in CFI layout
"""
__version__ = "0.1.0"
