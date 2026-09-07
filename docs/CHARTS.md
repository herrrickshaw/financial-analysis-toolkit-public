# Chart templates: data → analysis → visual

Every engine output has a fixed set of charts; each row says what data feeds it, what question it answers, and the form used.

## three_statement

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | revenue, net margin, cash, balance check | headline numbers, not a chart |
| Revenue and net earnings | IS rows | grouped columns: growth vs bottom line |
| Margin structure | gross / net margin | lines: profitability trend |
| Cash flow by activity | CFO / CFI / CFF | stacked columns: self-funding? |
| Cash bridge | opening → closing cash | waterfall: what moved cash |
| Asset composition | cash, AR, inventory, PP&E | stacked columns: capital deployment |
| Working-capital days | AR / inventory / AP days | lines: cash conversion |
| Leverage and coverage | debt/equity, interest cover | lines: de-risking |

## dcf

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | EV, value/share, upside, IRR | headline numbers |
| UFCF build | EBIT, taxes, D&A, capex, ΔNWC | stacked columns: what drives FCF |
| EV bridge | PV forecast, PV terminal, cash, debt | waterfall: forecast vs terminal, EV → equity |
| Terminal value cross-check | perpetuity vs multiple | columns: do the methods agree |
| Sensitivity heatmap | WACC × g grid | diverging heatmap centred on market price |
| Football field | valuation ranges vs price | range bars: where does value sit |

## lbo

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | IRR, MOIC, exit equity, entry multiple | headline numbers |
| Sources and uses | equity, tranches vs uses | stacked columns: funding structure |
| Debt paydown | tranche balances by year | stacked columns: deleveraging |
| EBITDA and leverage | EBITDA, NI, debt/EBITDA | columns + line |
| Returns attribution | EBITDA growth, multiple expansion, deleveraging | waterfall: source of equity gain |
| IRR sensitivity | scenario × exit multiple | heatmap (the workbook's data table) |

## merger

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | accretion %, premium, purchase multiple, new shares | headline numbers |
| EPS standalone vs combined | acquirer / target / combined EPS | columns: accretion / dilution |
| Contribution analysis | EBITDA, NI, ownership | stacked columns: who contributes vs who owns |
| Funding mix | cash / debt / stock | stacked column |
| Multiples | EV/EBITDA, P/E | grouped columns: re-rating |
| Accretion sensitivity | premium × % stock | diverging heatmap centred on zero |
| Pro forma accretion by year | reported vs adjusted | columns |
| Purchase price allocation | book value, write-ups, DTL, goodwill | waterfall |
| Pre-tax deal effects | synergies vs deal costs | stacked columns |
| Acquisition debt | balance and interest | columns |

## comps

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | current price, implied range, peer / deal counts | headline numbers |
| Football field | low–high implied price per method + current price | range bars |
| Peer EV multiples | EV/Revenue, EV/EBITDA per peer | grouped columns |
| Peer equity multiples | P/E per peer | grouped columns |
| Multiple statistics | 25th–75th percentile per multiple | range bars + stats table |
| Implied share price by multiple | p25–p75 implied price | range bars vs current |
| EV to equity bridge | cash, NOLs, debt, NCI … | waterfall |
| Precedent multiples | EV/Revenue, EV/EBITDA, EV/EBIT per deal | grouped columns |
| Offer premiums | 1-day / 1-week / 1-month | grouped columns |

## projection

| chart | data | analysis / form |
|---|---|---|
| KPI tiles | revenue, EBIT margin, cash, balance check | headline numbers |
| Revenue by product | product revenue | stacked columns: mix |
| Operating expenses | opex by category (top 7 + Other) | stacked columns |
| Headcount by type | payroll headcount | stacked columns |
| Profitability | gross / EBIT / net margin | lines |
| Cash flow by activity | CFO / CFI / CFF | stacked columns |
| Liquidity and leverage ratios | current, quick, D/E | lines |
