"""Reconciliation of finmodel.comps against the cached values of the BIWS 107-21 public comps workbook (Steel Dynamics),
the BIWS 107-27 Jazz precedent-transactions workbook and the CFI 'Comps, Precedents, Football Field' template.
The workbooks themselves are copyrighted and git-ignored; the reference numbers below were read from their cached values."""
import math
import pytest
from finmodel import comps
from finmodel.comps import Peer, Target, Deal, spread, implied_valuation, precedents, football_field, quartile_inc, stats, multiple, NM

# ---- BIWS Public-Comps: price, diluted shares, cash (positive), debt, preferred, NCI, revenue/EBITDA/NI LTM, FY17, FY18
BIWS_PEERS = [
    ("United States Steel Corp.", "X", 18.9, 165.6142, 820, 3140, 0, 1, (10327, 10545.15, 11231.27), (-128, 675, 921.38), (-1692, -74.89, 333.75)),
    ("Nucor Corporation", "NUE", 49.03, 318.3557, 2331.15, 4357.512, 0, 346.946, (15643.6, 16684.82, 16937.09), (1972.9, 2291.4, 2539.62), (469.6, 818.31, 1000.96)),
    ("Commercial Metals Company", "CMC", 15.5, 114.6286, 483.855, 1079.95, 0, 0.16, (4813.4, 4683.9467, 4780.1033), (431.9, 367.43, 423.1133), (129.4, 127.4067, 171.4867)),
    ("AK Steel Holding Corporation", "AKS", 4.35, 238.1962, 56.2, 2078.1, 0, 379.6, (6263.6, 5991.83, 6108.22), (547.2, 469.23, 580.9), (-135, 57.29, 128.85)),
    ("Worthington Industries, Inc.", "WOR", 43.29, 63.1153, 84.188, 583.96, 0, 126.48, (2819.7, 2891.3158, 2971.38), (239.9, 281.5267, 324.07), (143.7, 177.3525, 220.3308)),
    ("Reliance Steel & Aluminum Co.", "RS", 72.51, 72.5298, 116.5, 2169.4, 0, 28.6, (8679, 8890.36, 9303.56), (784.6, 850.74, 928.7), (313.1, 390.23, 441.55)),
]
PERIODS = ("ltm", "fy1", "fy2")
MULTS = {"EV / Revenue": ("ev", "revenue"), "EV / EBITDA": ("ev", "ebitda"), "P / E": ("equity", "net_income")}


def biws_peers():
    out = []
    for name, tk, px, sh, cash, debt, pref, nci, rev, ebitda, ni in BIWS_PEERS:
        m = {}
        for key, vals in (("revenue", rev), ("ebitda", ebitda), ("net_income", ni)):
            for per, v in zip(PERIODS, vals):
                m[f"{key}_{per}"] = v
        out.append(Peer(name, px, sh, cash=cash, debt=debt, preferred=pref, nci=nci, metrics=m, ticker=tk))
    return out


def biws_target():
    return Target("Steel Dynamics Inc.", 24.97, 242.017,
                  metrics={"revenue_ltm": 7307.2, "revenue_fy1": 7716.0164, "revenue_fy2": 8406.1512, "ebitda_ltm": 862.8, "ebitda_fy1": 626.3522,
                           "ebitda_fy2": 730.2372, "net_income_ltm": 12.1, "net_income_fy1": 170.7479, "net_income_fy2": 205.7727},
                  bridge={"cash": 1072.221, "equity_investments": 0, "other_non_core": 0, "nol": 61.148, "debt": -2700, "preferred": 0,
                          "nci": 11.231, "pensions": 0, "capital_leases": 0, "restructuring": 0})


def test_quartile_matches_excel_inclusive():
    assert quartile_inc([1, 2, 3, 4], 1) == 1.75 and quartile_inc([1, 2, 3, 4], 3) == 3.25
    s = stats([0.5279, 1.1495, 0.493, 0.5488, 1.1911, 0.8458])
    assert s["p75"] == pytest.approx(1.0736, abs=1e-4) and s["p25"] == pytest.approx(0.5331, abs=1e-4) and s["median"] == pytest.approx(0.6973, abs=1e-4)


def test_nm_rule():
    assert multiple(100, -5) == NM and multiple(1000, 5) == NM and multiple(100, 0) == "N/A" and multiple(100, None) == "N/A"
    assert multiple(100, 8) == 12.5


def test_biws_public_comps_spread():
    res = spread(biws_peers(), multiples=MULTS, periods=PERIODS)
    x = res["peers"][0]
    assert x["equity_value"] == pytest.approx(3130.1088, abs=1e-3) and x["enterprise_value"] == pytest.approx(5451.1088, abs=1e-3)
    assert x["multiples"]["EV / Revenue LTM"] == pytest.approx(0.5279, abs=1e-4)
    assert x["multiples"]["EV / EBITDA LTM"] == NM and x["multiples"]["P / E LTM"] == NM and x["multiples"]["P / E FY1"] == NM
    assert x["multiples"]["P / E FY2"] == pytest.approx(9.3786, abs=1e-4)
    nue = res["peers"][1]
    assert nue["multiples"]["P / E LTM"] == pytest.approx(33.2389, abs=1e-4)
    s = res["summary"]
    for label, (mx, p75, med, p25, mn) in {
        "EV / Revenue LTM": (1.1911, 1.0736, 0.6973, 0.5331, 0.493), "EV / Revenue FY2": (1.1303, 0.9935, 0.6759, 0.513, 0.4854),
        "EV / EBITDA LTM": (13.9996, 9.3559, 9.1146, 6.2823, 5.4943), "EV / EBITDA FY1": (11.9296, 8.4903, 7.9617, 7.4566, 6.4584),
        "P / E LTM": (33.2389, 22.5699, 17.9053, 16.0304, 13.7306), "P / E FY2": (15.594, 12.2782, 11.1357, 9.6242, 8.0415)}.items():
        assert (s[label]["max"], s[label]["p75"], s[label]["median"], s[label]["p25"], s[label]["min"]) == pytest.approx((mx, p75, med, p25, mn), abs=1e-4), label
    # operating stats (revenue growth etc. are template extras); EBITDA LTM stats
    assert res["operating_stats"]["ebitda_ltm"]["p75"] == pytest.approx(725.25, abs=1e-3)


def test_biws_valsum_implied_share_prices():
    res = spread(biws_peers(), multiples=MULTS, periods=PERIODS)
    iv = implied_valuation(biws_target(), res)
    assert iv["bridge_total"] == pytest.approx(-1555.4, abs=1e-6)
    rows = {r["multiple"]: r for r in iv["rows"]}
    r = rows["EV / Revenue LTM"]["implied"]
    assert r["min"]["enterprise_value"] == pytest.approx(3602.4373, abs=1e-3) and r["min"]["equity_value"] == pytest.approx(2047.0373, abs=1e-3)
    assert (r["min"]["share_price"], r["p25"]["share_price"], r["median"]["share_price"]) == pytest.approx((8.4582, 9.6689, 14.6271), abs=1e-4)
    assert r["min"]["premium_to_current"] == pytest.approx(-0.6613, abs=1e-4)
    assert (rows["EV / EBITDA LTM"]["implied"]["min"]["share_price"], rows["EV / EBITDA LTM"]["implied"]["median"]["share_price"]) == pytest.approx((13.1607, 26.0672), abs=1e-4)
    pe = rows["P / E FY2"]["implied"]
    assert (pe["min"]["share_price"], pe["p25"]["share_price"], pe["median"]["share_price"]) == pytest.approx((6.8373, 8.1829, 9.468), abs=1e-4)
    assert pe["min"]["equity_value"] == pytest.approx(1654.7309, abs=1e-3)   # P/E: equity = multiple × net income, no bridge


# ---- BIWS 107-27 Jazz precedent transactions
JAZZ = [
    ("AstraZeneca PLC", "Alexion Pharmaceuticals, Inc.", "2020-12-12", 40021.0911, 5862.4, 3061.8, 175.29, 120.98, 120.51, 127.62),
    ("Sanofi S.A.", "Bioverativ Inc.", "2018-01-22", 11037.76, 1168.5, 474.8, 105, 64.11, 63.75, 53.64),
    ("Shire plc", "Baxalta Incorporated", "2016-01-11", 35218.87, 6148, 2105, 45.57, 33.15, 30.6, 31.71),
    ("Allergan plc", "Allergan, Inc.", "2014-11-17", 68725.93, 7003.2, 2330, 219, 142, 123.97, 125.05),
    ("Bristol-Myers Squibb Company", "Amylin Pharmaceuticals, LLC", "2012-06-29", 6637.73, 651.65, -449.56, 31, 15.39, 15.27, 17.87),
    ("Fresenius Kabi USA, LLC", "Akorn, Inc.", "2017-04-24", 4789.02, 1101.92, 445.85, 34, 25.22, 24.08, 22.39),
    ("Lonza Group Ltd", "Capsugel Inc.", "2016-12-15", 5500, 1000, 344, None, None, None, None),
    ("Danaher Corporation", "Cepheid", "2016-09-06", 4078.76, 564.25, 0.588, 53, 34.42, 34.55, 35.84),
    ("Pfizer Inc.", "Medivation, Inc.", "2016-08-22", 14003.71, 1027.08, 456.48, 81.5, 37.39, 39.39, 35.77),
    ("AbbVie Inc.", "Pharmacyclics LLC", "2015-03-04", 20166.71, 816.12, 112.85, 261.25, 188.45, 167.18, 158.55),
    ("Valeant Pharmaceuticals", "Salix Pharmaceuticals Ltd.", "2015-02-22", 16137.23, 1133.54, 154.77, 173, 120.19, 118.09, 110.11),
    ("Merck & Co., Inc.", "Cubist Pharmaceuticals LLC", "2014-12-08", 9488.28, 1164.53, 203.55, 102, 74.36, 75.81, 70.75),
    ("Mallinckrodt", "Questcor Pharmaceuticals, Inc.", "2014-04-07", 5300.27, 890.9, 516.94, 86.1, 67.87, 62.12, 64.9),
    ("Allergan plc", "Forest Laboratories, LLC", "2014-02-18", 22128.81, 3371.42, 418.34, 89.48, 71.39, 68.89, 69.97),
    ("Forest Laboratories, LLC", "Aptalis Holdings Inc.", "2014-01-08", 2900, 700.18, 275.6, None, None, None, None),
    ("Amgen Inc.", "Onyx Pharmaceuticals, Inc.", "2013-08-25", 9253.84, 515.95, -151.48, 125, 86.82, 81.83, 96.31),
    ("Valeant Pharmaceuticals", "Medicis Pharmaceutical Corporation", "2012-09-03", 2328.78, 763.68, 191.39, 44, 31.56, 32.5, 32.92),
]


def jazz_deals():
    return [Deal(a, t, d, ev, ltm_revenue=rev, ltm_ebitda=e, offer_price=o, price_1d_prior=p1, price_1w_prior=p2, price_1m_prior=p3) for a, t, d, ev, rev, e, o, p1, p2, p3 in JAZZ]


def test_jazz_precedents():
    res = precedents(jazz_deals())
    d0 = res["deals"][0]
    assert d0["multiples"]["EV / Revenue LTM"] == pytest.approx(6.8267, abs=1e-4) and d0["multiples"]["EV / EBITDA LTM"] == pytest.approx(13.0711, abs=1e-4)
    assert d0["premiums"] == pytest.approx({"1-day": 0.4489, "1-week": 0.4546, "1-month": 0.3735}, abs=1e-4)
    assert res["deals"][4]["multiples"]["EV / EBITDA LTM"] == NM                    # negative EBITDA
    assert res["deals"][7]["multiples"]["EV / EBITDA LTM"] == NM                    # 6936x ≥ 100 cap
    assert res["deals"][6]["premiums"] == {}                                        # private target, no offer price
    s = res["summary"]
    assert (s["EV / Revenue LTM"]["max"], s["EV / Revenue LTM"]["p75"], s["EV / Revenue LTM"]["median"], s["EV / Revenue LTM"]["p25"], s["EV / Revenue LTM"]["min"]) == pytest.approx((24.7105, 10.186, 7.2286, 5.7285, 3.0494), abs=1e-4)
    assert (s["EV / EBITDA LTM"]["max"], s["EV / EBITDA LTM"]["p75"], s["EV / EBITDA LTM"]["median"], s["EV / EBITDA LTM"]["p25"], s["EV / EBITDA LTM"]["min"]) == pytest.approx((52.8967, 29.7915, 16.3597, 11.8111, 10.2532), abs=1e-4)
    p = res["premium_summary"]
    assert (p["1-day"]["max"], p["1-day"]["p75"], p["1-day"]["median"], p["1-day"]["p25"], p["1-day"]["min"]) == pytest.approx((1.1797, 0.541, 0.4394, 0.3732, 0.2534), abs=1e-4)
    assert p["1-month"]["p75"] == pytest.approx(0.6912, abs=1e-4)
    assert res["enterprise_value_stats"]["median"] == pytest.approx(9488.28, abs=1e-3)


# ---- CFI Comps / Precedents / Football Field template
CFI_PEERS = [("Micro Partners", 9.45, 100, 125, 267.5, 75.8865, 46.9298), ("Junior Enterprises", 5.68, 1250, 2000, 4136.3636, 777.7778, 411.7647),
             ("Minature Company", 18.11, 50, 25, 443.0952, 95.9278, 55.7186), ("Average Limited", 12.27, 630, 350, 1949.4898, 527.7624, 293.9231),
             ("Bohemeth Industires", 9.03, 1500, 0, 6622, 794.64, 422.6809)]
CFI_MULTS = {"EV / Revenue": ("ev", "revenue"), "EV / EBITDA": ("ev", "ebitda"), "P / E": ("ev", "net_income")}   # template computes 'P/E' as EV / earnings


def test_cfi_football_field():
    peers = [Peer(n, px, sh, net_debt=nd, metrics={"revenue": r, "ebitda": e, "net_income": ni}) for n, px, sh, nd, r, e, ni in CFI_PEERS]
    c = spread(peers, multiples=CFI_MULTS)
    assert c["peers"][0]["enterprise_value"] == pytest.approx(1070) and c["peers"][0]["multiples"]["P / E LTM"] == pytest.approx(22.8, abs=1e-4)
    assert (c["summary"]["EV / Revenue LTM"]["mean"], c["summary"]["EV / EBITDA LTM"]["mean"], c["summary"]["P / E LTM"]["mean"]) == pytest.approx((2.898, 13.5711, 24.2272), abs=1e-4)
    assert (c["summary"]["EV / Revenue LTM"]["median"], c["summary"]["EV / EBITDA LTM"]["median"], c["summary"]["P / E LTM"]["median"]) == pytest.approx((2.2, 14.1, 22.8), abs=1e-4)
    deals = [Deal("Average Limited", "Current Ltd", "2017-01-24", 2350, multiples={"EV / Revenue LTM": 1.9, "EV / EBITDA LTM": 9.4, "EV / EBIT LTM": 11.21}),
             Deal("Bohemeth Industires", "Recent Inc", "2016-04-19", 6500, multiples={"EV / Revenue LTM": 1.4, "EV / EBITDA LTM": 8.04, "EV / EBIT LTM": 12.63}),
             Deal("Other Group", "Past Co", "2014-04-19", 2150, multiples={"EV / Revenue LTM": 1.27, "EV / EBITDA LTM": 8.65, "EV / EBIT LTM": 12.08}),
             Deal("Junior Enterprises", "Historical LLP", "2014-11-07", 450, multiples={"EV / Revenue LTM": 2.29, "EV / EBITDA LTM": 11.06, "EV / EBIT LTM": 13.59}),
             Deal("Minature Company", "Old Group", "2012-11-01", 325, multiples={"EV / Revenue LTM": 5.09, "EV / EBITDA LTM": 18.75, "EV / EBIT LTM": 21.53}),
             Deal("Micro Partners", "Dated Enterprises", "2011-10-07", 150, multiples={"EV / Revenue LTM": 2.1, "EV / EBITDA LTM": 9.3, "EV / EBIT LTM": 13.2})]
    p = precedents(deals)
    assert (p["summary"]["EV / Revenue LTM"]["mean"], p["summary"]["EV / EBITDA LTM"]["mean"], p["summary"]["EV / EBIT LTM"]["mean"]) == pytest.approx((2.3417, 10.8667, 14.04), abs=1e-4)
    assert (p["summary"]["EV / Revenue LTM"]["median"], p["summary"]["EV / EBIT LTM"]["median"]) == pytest.approx((2, 12.915), abs=1e-4)
    target = Target("Target Co", 25, 20000, metrics={"revenue": 400000, "ebitda": 60000, "ebit": 45000, "net_income": 20000}, net_debt=250000 - 75000)
    iv = implied_valuation(target, c, stat_keys=("mean",), multiples={"EV / Revenue": ("ev", "revenue"), "EV / EBITDA": ("ev", "ebitda"), "P / E": ("equity", "net_income")})
    rows = {r["multiple"]: r["implied"]["mean"] for r in iv["rows"]}
    assert rows["EV / Revenue LTM"]["enterprise_value"] == pytest.approx(1159214.4008, rel=1e-6) and rows["EV / Revenue LTM"]["equity_value"] == pytest.approx(984214.4008, rel=1e-6)
    assert (rows["EV / Revenue LTM"]["share_price"], rows["EV / EBITDA LTM"]["share_price"], rows["P / E LTM"]["share_price"]) == pytest.approx((49.2107, 31.9633, 24.2272), abs=1e-4)
    ff = football_field(target, {"Comps": c, "Precedents": p}, {"DCF - base case": (28, 36), "DCF - blue sky": (36, 44), "52 wk hi/lo": (22, 30)}, stat_low="mean", stat_high="mean",
                        multiples={"Comps": {"EV / Revenue": ("ev", "revenue"), "EV / EBITDA": ("ev", "ebitda"), "P / E": ("equity", "net_income")}})
    items = {i["method"]: i for i in ff["items"]}
    assert (items["Comps"]["low"], items["Comps"]["high"]) == pytest.approx((24.2272, 49.2107), abs=1e-4)
    assert (items["Precedents"]["low"], items["Precedents"]["high"]) == pytest.approx((22.84, 38.0833), abs=1e-4)
    assert items["52 wk hi/lo"]["low"] == 22 and ff["current_price"] == 25


def test_from_dict_roundtrip():
    d = {"target": {"name": "T", "price": 10, "diluted_shares": 100, "metrics": {"revenue": 1000, "ebitda": 100, "net_income": 50}, "bridge": {"cash": 50, "debt": -200}},
         "peers": [{"name": "A", "price": 20, "diluted_shares": 50, "cash": 10, "debt": 100, "metrics": {"revenue": 900, "ebitda": 90, "net_income": 40}},
                   {"name": "B", "price": 30, "diluted_shares": 40, "cash": 20, "debt": 50, "metrics": {"revenue": 1200, "ebitda": 150, "net_income": 70}}],
         "deals": [{"acquirer": "X", "target": "Y", "date": "2024-01-01", "enterprise_value": 1500, "ltm_revenue": 1000, "ltm_ebitda": 120, "offer_price": 12, "price_1d_prior": 10}],
         "extra_ranges": {"DCF": [9, 14]}}
    out = comps.from_dict(d)
    assert set(out) == {"comps", "implied_from_comps", "precedents", "implied_from_precedents", "football_field"}
    assert len(out["football_field"]["items"]) == 3
    assert out["precedents"]["deals"][0]["premiums"]["1-day"] == pytest.approx(0.2)
