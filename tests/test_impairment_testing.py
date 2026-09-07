"""finmodel.impairment_testing: the three real ASC 350/350-30/360 tests are checked for their DIFFERENCES, not
just their happy paths -- goodwill's real cap at the existing balance, and ASC 360's real two-step structure
(an asset can be economically underwater on a fair-value basis and still pass Step 1 on an undiscounted basis)."""
import pytest

from finmodel import impairment_testing as IT


def test_goodwill_impairment_uncapped_case():
    out = IT.goodwill_impairment_test(reporting_unit_fair_value=80.0, reporting_unit_carrying_value=95.0, goodwill_balance=30.0)
    assert out["impaired"] is True
    assert out["impairment_loss"] == 15.0
    assert out["capped_by_goodwill_balance"] is False
    assert out["remaining_goodwill"] == 15.0


def test_goodwill_impairment_real_cap_at_existing_balance():
    # excess of carrying over fair value (25) EXCEEDS the goodwill balance (20) -- goodwill can't go negative;
    # a real, load-bearing detail of ASC 350, not a rounding edge case.
    out = IT.goodwill_impairment_test(reporting_unit_fair_value=70.0, reporting_unit_carrying_value=95.0, goodwill_balance=20.0)
    assert out["excess_of_carrying_over_fair_value"] == 25.0
    assert out["impairment_loss"] == 20.0
    assert out["capped_by_goodwill_balance"] is True
    assert out["remaining_goodwill"] == 0.0


def test_goodwill_no_impairment_when_fair_value_exceeds_carrying():
    out = IT.goodwill_impairment_test(reporting_unit_fair_value=100.0, reporting_unit_carrying_value=90.0, goodwill_balance=15.0)
    assert out["impaired"] is False
    assert out["impairment_loss"] == 0.0
    assert out["remaining_goodwill"] == 15.0


def test_indefinite_lived_intangible_direct_comparison_no_recoverability_screen():
    out = IT.indefinite_lived_intangible_impairment_test(fair_value=8.0, carrying_value=10.0)
    assert out["impaired"] is True
    assert out["impairment_loss"] == 2.0
    assert out["remaining_carrying_value"] == 8.0


def test_long_lived_asset_step1_fails_measures_loss_in_step2():
    out = IT.long_lived_asset_impairment_test(undiscounted_cash_flows=[3.0, 3.0, 3.0, 3.0], carrying_value=15.0, fair_value=9.0)
    assert out["total_undiscounted_cash_flows"] == 12.0
    assert out["step1_recoverable"] is False
    assert out["impaired"] is True
    assert out["impairment_loss"] == 6.0


def test_long_lived_asset_step1_passes_even_though_fair_value_is_below_carrying():
    # the single most commonly confused real detail: undiscounted CF (16) >= carrying value (15) means Step 1
    # PASSES and no loss is measured, even though fair value (9) is well below carrying value -- a deliberate,
    # conservative bright-line screen, not a bug.
    out = IT.long_lived_asset_impairment_test(undiscounted_cash_flows=[4.0, 4.0, 4.0, 4.0], carrying_value=15.0, fair_value=9.0)
    assert out["total_undiscounted_cash_flows"] == 16.0
    assert out["step1_recoverable"] is True
    assert out["impaired"] is False
    assert out["impairment_loss"] == 0.0


def test_from_dict_bundles_all_three_tests():
    d = {"goodwill": {"reporting_unit_fair_value": 70.0, "reporting_unit_carrying_value": 95.0, "goodwill_balance": 20.0},
         "indefinite_lived_intangible": {"fair_value": 8.0, "carrying_value": 10.0},
         "long_lived_asset": {"undiscounted_cash_flows": [3.0, 3.0], "carrying_value": 15.0, "fair_value": 9.0}}
    out = IT.from_dict(d)
    assert out["goodwill"]["impairment_loss"] == 20.0
    assert out["indefinite_lived_intangible"]["impairment_loss"] == 2.0
    assert out["long_lived_asset"]["impaired"] is True
