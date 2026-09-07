import pytest
from finmodel import projection as pj


def test_projection_balances_and_flows(projection_inputs):
    r = pj.from_dict(projection_inputs)
    assert r["years"] == [2025, 2026, 2027, 2028, 2029]
    assert r["balanced"], r["balance_sheet"]["Check"]
    IS, BS, CF = r["income_statement"], r["balance_sheet"], r["cash_flow"]
    # revenue = sum over products of price*units ; base year from monthly units
    p1 = r["sales"]["Product 1"]
    assert p1["units"][0] == sum(projection_inputs["products"][0]["units_by_month"])
    assert p1["units"][1] == pytest.approx(p1["units"][0] * 1.05)
    assert IS["Revenue"][0] == pytest.approx(sum(s["revenue"][0] for s in r["sales"].values()))
    # cash ties: closing cash on BS == CF closing
    assert BS["Cash"] == pytest.approx(CF["Closing Cash Balance"])
    # retained earnings roll
    assert BS["Retained Earnings"][1] - BS["Retained Earnings"][0] == pytest.approx(IS["Net Earnings"][1])
    # PP&E roll-forward with derived D&A rate
    sch = r["schedules"]["ppe"]
    assert sch["da_pct_ppe"] == pytest.approx(30000 / 300000)
    assert sch["Closing"][1] == pytest.approx(sch["Closing"][0] + 40000 - sch["Closing"][0] * 0.1)
    # debt repayment shows up in year 3 (index 3) and interest follows opening debt
    assert r["schedules"]["debt"]["Closing"][3] == pytest.approx(150000)
    assert IS["Interest Expense"][4] == pytest.approx(150000 * 12000 / 200000)
    # bonus pool 10% of positive EBIT, deducted before tax
    assert IS["Employee Bonuses"][0] == pytest.approx(max(IS["EBIT"][0], 0) * 0.1)
    assert IS["EBT"][0] == pytest.approx(IS["EBIT"][0] - IS["Employee Bonuses"][0] - IS["Interest Expense"][0])
    assert IS["Income Taxes"][0] == pytest.approx(max(IS["EBT"][0], 0) * 0.2)


def test_payroll_workdays_and_hours(projection_inputs):
    r = pj.from_dict(projection_inputs)
    ft = r["payroll"]["types"]["Full-Time"]
    assert r["payroll"]["work_days"][0] == 261  # 2025 has 261 weekdays
    assert ft["headcount"][0] == 4
    assert ft["hours_per_head_base"] == pytest.approx(8 * 261)
    assert ft["wages"][0] == pytest.approx(8 * 261 * (32 + 48 + 60 + 30))
    # forecast wage = avg wage * hours/head * headcount * workday ratio  (includes hours/day, unlike the CFI sheet)
    exp = ft["avg_hourly_wage"][1] * ft["hours_per_head_base"] * ft["headcount"][1] * r["payroll"]["work_days"][1] / 261
    assert ft["wages"][1] == pytest.approx(exp)
    pt = r["payroll"]["types"]["Part-Time"]
    assert pt["wages"][0] == pytest.approx(80 * 12 * 22)
    assert r["payroll"]["insurance"][0] == pytest.approx(ft["wages"][0] * 0.016)  # benefits only for full-time


def test_wage_expense_basis_switch(projection_inputs):
    gross = pj.from_dict(projection_inputs)
    net = pj.from_dict({**projection_inputs, "wage_expense_basis": "net_pay"})
    assert net["income_statement"]["EBIT"][0] > gross["income_statement"]["EBIT"][0]
    assert net["balanced"]
