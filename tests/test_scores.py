from finmodel.scores import altman_z, beneish_m, piotroski_f, health


CUR = {"revenue": 1000, "cogs": 600, "operating_income": 150, "net_income": 100, "cfo": 130, "da": 40, "total_assets": 1200, "current_assets": 500,
       "current_liabilities": 300, "receivables": 120, "ppe": 500, "equity": 600, "retained_earnings": 400, "debt_total": 250, "total_liabilities": 600, "diluted_shares": 100, "sga": 150}
PREV = {"revenue": 900, "cogs": 560, "operating_income": 120, "net_income": 80, "cfo": 100, "da": 38, "total_assets": 1100, "current_assets": 450,
        "current_liabilities": 290, "receivables": 110, "ppe": 480, "equity": 520, "retained_earnings": 320, "debt_total": 260, "total_liabilities": 580, "diluted_shares": 100, "sga": 140}


def test_altman_public_hand_calc():
    z = altman_z(CUR, market_cap=1500)
    # 1.2*(200/1200) + 1.4*(400/1200) + 3.3*(150/1200) + 0.6*(1500/600) + 1000/1200
    assert abs(z["z"] - (1.2 * 200 / 1200 + 1.4 * 400 / 1200 + 3.3 * 150 / 1200 + 0.6 * 1500 / 600 + 1000 / 1200)) < 1e-12
    assert z["zone"] == "safe"
    assert altman_z({"total_assets": 1000, "current_assets": 100, "current_liabilities": 400, "retained_earnings": -300, "operating_income": -50, "revenue": 300, "equity": 100, "total_liabilities": 900}, 50)["zone"] == "distress"
    assert altman_z(CUR, variant="private")["variant"] == "private" and "sales/TA" in altman_z(CUR, variant="nonmfg")["components"]


def test_beneish_neutral_when_nothing_changes():
    m = beneish_m(CUR, CUR)
    comp = m["components"]
    assert all(abs(comp[k] - 1.0) < 1e-12 for k in ("DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI"))
    assert abs(comp["TATA"] - (100 - 130) / 1200) < 1e-12
    assert m["likely_manipulator"] is False


def test_piotroski_counts_signals():
    p = piotroski_f(CUR, PREV)
    s = p["signals"]
    assert s["ROA > 0"] and s["CFO > 0"] and s["CFO > net income (accruals)"] and s["Leverage falling"] and s["No new shares"]
    assert s["Current ratio rising"] is (500 / 300 > 450 / 290)
    assert p["f"] == sum(s.values()) and p["grade"] in ("strong", "middle", "weak")
    assert set(health(CUR, PREV, 1500)) == {"altman", "beneish", "piotroski"}
