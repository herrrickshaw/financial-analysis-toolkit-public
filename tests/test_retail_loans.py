"""finmodel.retail_loans: EMI is checked against the standard closed-form reducing-balance formula
(independently of finmodel.fin.pmt, which the module itself calls); prepayment and floating-rate-reset are
checked against their defining real properties (reduce-tenure always saves at least as much interest as
reduce-emi for the same prepayment; a lower reset rate always lowers the re-computed EMI); and loan
eligibility is checked with an exact round-trip back through the EMI formula."""
import pytest

from finmodel import retail_loans as RL


def test_emi_matches_the_standard_closed_form():
    principal, annual_rate, tenure_months = 1_000_000.0, 0.09, 240
    r = annual_rate / 12
    expected = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
    assert RL.emi(principal, annual_rate, tenure_months) == pytest.approx(expected)


def test_amortization_schedule_identities():
    out = RL.amortization_schedule(1_000_000.0, 0.09, 240)
    assert out["schedule"][0]["interest"] == pytest.approx(1_000_000.0 * 0.09 / 12)
    assert out["schedule"][-1]["closing_balance"] == pytest.approx(0.0, abs=1e-3)
    assert out["total_payment"] == pytest.approx(1_000_000.0 + out["total_interest"])
    assert sum(r["principal"] for r in out["schedule"]) == pytest.approx(1_000_000.0, abs=1e-3)


def test_prepayment_reduce_tenure_saves_at_least_as_much_interest_as_reduce_emi():
    kwargs = dict(principal=1_000_000.0, annual_rate=0.09, tenure_months=240, prepayment_amount=200_000.0, prepayment_month=24)
    reduce_tenure = RL.prepayment_impact(**kwargs, strategy="reduce_tenure")
    reduce_emi = RL.prepayment_impact(**kwargs, strategy="reduce_emi")
    assert reduce_tenure["interest_saved"] > reduce_emi["interest_saved"] > 0
    assert reduce_tenure["new_tenure_months"] < 240
    assert reduce_emi["new_tenure_months"] == 240  # tenure unchanged by construction
    assert reduce_emi["new_emi"] < RL.emi(1_000_000.0, 0.09, 240)


def test_prepayment_that_clears_the_loan_early():
    out = RL.prepayment_impact(principal=1_000_000.0, annual_rate=0.09, tenure_months=240,
                               prepayment_amount=990_000.0, prepayment_month=12, strategy="reduce_tenure")
    assert out["loan_fully_repaid"] is True
    assert out["interest_saved"] > 0


def test_prepayment_rejects_bad_strategy_and_bad_month():
    with pytest.raises(ValueError):
        RL.prepayment_impact(principal=1.0, annual_rate=0.1, tenure_months=12, prepayment_amount=0.1,
                             prepayment_month=1, strategy="bogus")
    with pytest.raises(ValueError):
        RL.prepayment_impact(principal=1.0, annual_rate=0.1, tenure_months=12, prepayment_amount=0.1, prepayment_month=12)


def test_floating_rate_reset_lower_rate_lowers_the_reduce_emi_payment():
    lower = RL.floating_rate_reset(outstanding_balance=800_000.0, remaining_tenure_months=180, old_rate=0.10, new_rate=0.08)
    higher = RL.floating_rate_reset(outstanding_balance=800_000.0, remaining_tenure_months=180, old_rate=0.10, new_rate=0.12)
    assert lower["new_emi"] < higher["new_emi"]


def test_floating_rate_reset_reduce_tenure_requires_current_emi():
    with pytest.raises(ValueError):
        RL.floating_rate_reset(outstanding_balance=800_000.0, remaining_tenure_months=180, old_rate=0.10,
                               new_rate=0.08, strategy="reduce_tenure")
    out = RL.floating_rate_reset(outstanding_balance=800_000.0, remaining_tenure_months=180, old_rate=0.10,
                                 new_rate=0.08, strategy="reduce_tenure", current_emi=9000.0)
    assert out["new_tenure_months"] < 180  # a lower rate at the same EMI pays off sooner


def test_foreclosure_payoff_outstanding_decreases_with_later_foreclosure_month():
    early = RL.foreclosure_payoff(1_000_000.0, 0.09, 240, foreclosure_month=12)
    late = RL.foreclosure_payoff(1_000_000.0, 0.09, 240, foreclosure_month=120)
    assert early["outstanding_balance"] > late["outstanding_balance"]
    at_maturity = RL.foreclosure_payoff(1_000_000.0, 0.09, 240, foreclosure_month=240)
    assert at_maturity["outstanding_balance"] == pytest.approx(0.0, abs=1e-3)


def test_loan_eligibility_foir_round_trips_through_emi():
    out = RL.loan_eligibility_foir(monthly_gross_income=150_000.0, existing_emis=20_000.0,
                                   annual_rate=0.09, tenure_months=240, foir_limit=0.50)
    assert out["max_total_emi"] == pytest.approx(75_000.0)
    assert out["available_emi_capacity"] == pytest.approx(55_000.0)
    reconstructed_emi = RL.emi(out["max_eligible_principal"], 0.09, 240)
    assert reconstructed_emi == pytest.approx(out["available_emi_capacity"])


def test_from_dict_bundles_everything():
    out = RL.from_dict({"emi_calculation": {"principal": 100000.0, "annual_rate": 0.10, "tenure_months": 12}})
    assert out["emi_calculation"]["emi"] > 0
