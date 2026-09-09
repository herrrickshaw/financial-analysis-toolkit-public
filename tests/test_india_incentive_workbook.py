"""finmodel.india_incentive_workbook: checks that every sheet is present with the expected row counts, that
the transcribed catalog data's header/row shapes are internally consistent (every row has the same number of
columns as its sheet's header), and that the 28-State Matrix sheet's numbers are computed live and match
what finmodel.sector_investment_model/project_bankability themselves produce from the same example files --
not independently re-typed into this module."""
import json

from openpyxl import load_workbook

from finmodel import india_incentive_workbook as WB
from finmodel import sector_investment_model as SIM
from finmodel import project_bankability as PB


def test_every_catalog_row_matches_its_headers_length():
    for headers, rows in [
        (WB.STATE_INCENTIVES_HEADERS, WB.STATE_INCENTIVES_ROWS),
        (WB.CENTRAL_INCENTIVES_HEADERS, WB.CENTRAL_INCENTIVES_ROWS),
        (WB.LAND_COST_HEADERS, WB.LAND_COST_ROWS),
    ]:
        for row in rows:
            assert len(row) == len(headers)


def test_state_incentives_covers_all_29_states():
    states = {row[0] for row in WB.STATE_INCENTIVES_ROWS}
    assert states == {"Madhya Pradesh", "Gujarat", "Maharashtra", "Tamil Nadu", "Uttar Pradesh", "Rajasthan",
                      "Karnataka", "Telangana", "Andhra Pradesh", "Odisha", "Haryana", "Punjab",
                      "Kerala", "West Bengal", "Bihar", "Assam", "Delhi (NCT)", "Chandigarh (UT)",
                      "Himachal Pradesh", "Uttarakhand", "Jharkhand", "Chhattisgarh", "Goa",
                      "Jammu & Kashmir", "Ladakh", "Puducherry (UT)",
                      "Dadra & Nagar Haveli and Daman & Diu (UT)",
                      "Andaman & Nicobar Islands and Lakshadweep (UTs)"}


def test_matrix_rows_match_the_underlying_modules_directly():
    matrix_rows = WB._matrix_and_bankability_rows()
    with open(WB._EXAMPLES / "state_sector_matrix_demo.json") as f:
        matrix = SIM.from_dict(json.load(f))["sample_project_matrix"]
    with open(WB._EXAMPLES / "project_bankability_demo.json") as f:
        bankability = PB.from_dict(json.load(f))["rank_projects"]
    irr_by_state = {p["state"]: p for p in bankability["projects"]}

    # 28 state rows + 1 TOTAL row
    assert len(matrix_rows["rows"]) == 29
    by_state = {row[0]: row for row in matrix_rows["rows"][:-1]}
    for p in matrix["projects"]:
        row = by_state[p["state"]]
        assert row[3] == round(p["capex"]["total_capex"], 2)
        assert row[7] == round(irr_by_state[p["state"]]["irr_without_incentives"], 4)
    total_row = matrix_rows["rows"][-1]
    assert total_row[0] == "TOTAL (28 states)"
    assert total_row[3] == round(matrix["total_capex_across_projects"], 2)


def test_build_workbook_writes_all_sheets(tmp_path):
    path = WB.build_workbook(str(tmp_path / "india_incentives.xlsx"))
    wb = load_workbook(path)
    assert wb.sheetnames == ["README", "State Incentives", "Central Incentives", "Land Cost Benchmarks",
                             "28-State Matrix", "Tax Regime Comparison", "Financing Effects"]
    assert wb.properties.title == WB.WORKBOOK_TITLE == "Investment Promotion Agency (IPA) Support"
    tax_sheet = wb["Tax Regime Comparison"]
    assert tax_sheet.max_row == 4  # header + 3 regimes
    financing_sheet = wb["Financing Effects"]
    assert financing_sheet.max_row == 5  # header + 2 CGTMSE rows + 2 IREDA rows
    ws = wb["28-State Matrix"]
    assert ws.cell(row=1, column=1).value == "State"
    assert ws.cell(row=30, column=1).value == "TOTAL (28 states)"
    states_sheet = wb["State Incentives"]
    assert states_sheet.max_row == 1 + len(WB.STATE_INCENTIVES_ROWS)
    central_sheet = wb["Central Incentives"]
    assert central_sheet.max_row == 1 + len(WB.CENTRAL_INCENTIVES_ROWS)
