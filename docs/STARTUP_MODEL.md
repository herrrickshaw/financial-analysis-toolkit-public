# Startup / new-business model (`finmodel.startup_model`)

A generator for a hypothetical new business's three-statement projection and DCF valuation, plus a real-data
sanity check: does the plan's assumed exit-year margin look anything like what real, mature companies in that
sector actually report?

**Everything about the business plan itself is illustrative** — `examples/startup_saas.json`'s revenue ramp,
margins and funding rounds are a scenario, not a real company's numbers, the same way a bank's illustrative DCF
growth assumption is labeled illustrative elsewhere in this toolkit. What is NOT illustrative is the benchmark:
it reads the real SEC-filed margins already sitting in `data/edgar/*.json` from the seven football-field sector
checks (`docs/FOOTBALL_FIELD_*.md`), so a founder's assumption gets checked against real market data, not a
made-up "typical startup" range.

## Why this doesn't duplicate the existing engines

No new modeling math was written for the three-statement or DCF pieces:

- `build_three_statement()` is a translation layer onto `finmodel.three_statement` — the same linked
  income-statement/balance-sheet/cash-flow engine that reconciles to the CFI "Case Study - Three Statement
  Model" workbook cell-for-cell (`tests/test_three_statement.py`). A startup's high-level assumptions (a revenue
  ramp, a gross-margin trajectory, payroll and other-opex as % of revenue, funding rounds) get converted into
  that engine's `HistoricalYear`/`ForecastAssumptions` inputs.
- `dcf_from_projection()` is a translation layer onto `finmodel.dcf` — the same unlevered DCF (mid-year
  convention, XNPV, perpetuity/multiple/average terminal value) every real-company football-field check uses.
  EBIT is EBT plus the interest add-back, D&A/capex/ΔNWC come straight from the projection's own schedules.
- `benchmark_against_sector()` is the one genuinely new piece: it reads the real per-sector peer tickers this
  repo already validated (steel, oil & gas, software, banking, REITs, airlines, insurance) and reports the
  startup's assumed terminal-year margin against those real companies' most recent actual fiscal year.

## A worked example (`examples/startup_saas.json`)

A hypothetical B2B SaaS business: $200K of beta revenue in year 0, ramping to a targeted $20M by year 5, with
gross margin improving 65%→80% and combined opex (payroll + other) falling from 140% of revenue to 55% as the
business scales — a standard early-SaaS operating-leverage story, not a real company's plan.

```bash
finmodel startup examples/startup_saas.json --json-out out/startup_saas.json
```

```
                             0             1             2             3             4             5
Revenue                200,000       800,000     2,500,000     6,000,000    12,000,000    20,000,000
Gross Profit                 0       520,000     1,750,000     4,440,000     9,240,000    16,000,000
Net Earnings                 0      -503,625      -716,629      -313,309     1,092,218     3,868,564
Cash                 3,000,000     2,442,259     9,536,796     8,775,149     9,043,717    11,730,981
Balance sheet balances: True
DCF: enterprise value 2,400,647  equity value 5,400,647  per share 0.5401
Benchmark vs real software peers (operating_income/revenue, FY5): this plan 24.5% vs real range 17.2%-46.8% → within the real range these peers actually reported
```

## Reading the output

**Three-statement**: `year0` is "day one" — the company incorporates, its founders/seed investors contribute
`starting_cash` (+ the value of any `starting_ppe`, modeled as equity funding a same-day equipment purchase, not
a free non-cash gift — see the note in `finmodel/startup_model.py` on why that distinction matters for the cash
roll-forward), and the P&L nets to exactly zero (it's a balance-sheet snapshot, not a modeled operating period).
From year 1 the engine compounds revenue, applies the margin/opex trajectory, and rolls AR/AP/inventory,
PP&E/D&A, debt and cash forward exactly as `finmodel.three_statement` always does. `Balance sheet balances: True`
means the same `Total Assets == Total Liabilities + Equity` check every other engine check in this repo enforces
— not a weaker, startup-specific pass.

**DCF**: cash burn is real in the early years here (UFCF is negative through year 3 — a genuine, unglamorous
fact about a business that's still investing in growth), so enterprise value at a 30% venture-style discount
rate is much lower than the eventual cash the business could generate; equity value stays positive because
`starting_cash` and the funding round net out against that burn in the DCF's cash/debt bridge. A steeper burn
or a lower funding cushion would show up here as a negative equity value — the same honest signal the airline
check's "naive" black-swan DCF scenario produced (`docs/FOOTBALL_FIELD_ALK.md` §3): the number isn't wrong, it's
telling you the assumption combination doesn't cash-flow.

**Benchmark**: this example's assumed FY5 operating margin (24.5%) sits inside the real range reported by six
real, large-cap software companies' own most recent 10-Ks, ranked low to high — IBM 17.2%, Salesforce 20.1%,
Cisco 24.3%, Oracle 30.6%, Adobe 36.6%, Microsoft 46.8%. A margin outside that real range isn't necessarily wrong
— a startup can plausibly beat
or fall short of incumbents — but it's a flag worth noticing rather than a silently-accepted assumption. Pick
`--benchmark-sector` (or `benchmark_sector` in the input JSON) from whichever of the seven validated sectors is
the closest real-world comparison for the business being modeled; `benchmark_against_sector()` raises rather
than fabricating a range for a sector this repo hasn't collected real peer data for yet.

## Input reference

See `finmodel/startup_model.py`'s `StartupInputs` dataclass for the full field list. The two ways to specify
growth: `revenue_growth` (a rate per forecast year, compounding off `year0_revenue` — requires a nonzero seed)
or `revenue_path` (absolute revenue per forecast year — the more natural input when a plan already states
"$800K in year 1, $2.5M in year 2, …" directly, and the only option for a genuinely pre-revenue business with
`year0_revenue=0`). `equity_raised`/`debt_raised` are `{forecast_year_index: amount}` maps (0-based; index 0 is
the first forecast year) for modeling a specific funding round landing in a specific year rather than smoothing
it into the ongoing cash-flow assumptions.

**Try it.** `python -m finmodel.cli startup examples/startup_saas.json --benchmark-sector airline` to see the
same plan checked against a completely different real sector's margins (a deliberately poor fit, to see what an
"OUTSIDE the real range" flag looks like) instead of software's.
