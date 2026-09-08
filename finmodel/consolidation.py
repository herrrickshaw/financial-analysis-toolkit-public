"""Consolidation accounting and noncontrolling interest (ASC 810) -- the real mechanic every parent company
with a majority-owned (but not wholly-owned) subsidiary applies: US GAAP requires FULL consolidation of the
subsidiary's financials (100% of its revenue, expenses, assets and liabilities line by line), with a
separate Noncontrolling Interest (NCI) line carving out the portion attributable to minority shareholders.
No prior representation across the toolkit's other ~50 modules, which price and structure deals
(`finmodel.merger`, `finmodel.ppa_valuation`) without ever consolidating a less-than-wholly-owned subsidiary
afterward.

  * Consolidated net income = the parent's own standalone net income + 100% of the subsidiary's net income
    (not just the parent's proportionate share) -- then NCI's share is carved OUT afterward, not excluded
    from the top line, which is the real, defining difference from simple proportionate consolidation.
  * NCI's share of net income = subsidiary net income x NCI ownership %; net income ATTRIBUTABLE TO THE
    PARENT (the number that actually drives the parent's own EPS) is the consolidated total less that carve-out.
  * NCI also appears on the consolidated balance sheet, in the EQUITY section (not as a liability) -- the
    subsidiary's total equity x the NCI ownership %.
  * At acquisition, US GAAP's default (ASC 805) measures NCI at its own acquisition-date FAIR VALUE (the
    "full goodwill" method, implicitly grossing up goodwill for the NCI's share too) -- a real, deliberately
    DIFFERENT convention from IFRS, which lets an acquirer elect instead to measure NCI at its proportionate
    share of the subsidiary's identifiable net assets (the "partial goodwill" method), producing a smaller
    NCI balance and a smaller total goodwill figure for the exact same deal.
"""
from __future__ import annotations

from typing import Any, Dict


def consolidated_net_income(parent_standalone_net_income: float, subsidiary_net_income: float,
                            nci_ownership_pct: float) -> Dict[str, Any]:
    nci_share_of_net_income = subsidiary_net_income * nci_ownership_pct
    consolidated_ni = parent_standalone_net_income + subsidiary_net_income
    return {"consolidated_net_income": consolidated_ni, "nci_share_of_net_income": nci_share_of_net_income,
            "net_income_attributable_to_parent": consolidated_ni - nci_share_of_net_income}


def nci_balance_sheet(subsidiary_total_equity: float, nci_ownership_pct: float) -> Dict[str, Any]:
    nci_balance = subsidiary_total_equity * nci_ownership_pct
    return {"nci_balance": nci_balance, "parent_share_of_subsidiary_equity": subsidiary_total_equity - nci_balance}


def nci_at_acquisition_fair_value_method(subsidiary_fair_value: float, nci_ownership_pct: float) -> Dict[str, Any]:
    return {"nci_initial_value": subsidiary_fair_value * nci_ownership_pct, "method": "fair_value (US GAAP default)"}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "consolidated_net_income" in d:
        out["consolidated_net_income"] = consolidated_net_income(**d["consolidated_net_income"])
    if "nci_balance_sheet" in d:
        out["nci_balance_sheet"] = nci_balance_sheet(**d["nci_balance_sheet"])
    if "nci_at_acquisition_fair_value_method" in d:
        out["nci_at_acquisition_fair_value_method"] = nci_at_acquisition_fair_value_method(**d["nci_at_acquisition_fair_value_method"])
    return out
