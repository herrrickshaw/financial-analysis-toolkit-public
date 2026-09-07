"""Inventory costing: FIFO, LIFO, and weighted-average cost-flow assumptions -- the real, standard
accounting choice (ASC 330; LIFO is US-GAAP-only, disallowed under IFRS) for splitting the total cost of
goods available for sale between cost of goods sold and ending inventory, with no prior representation
across the toolkit's other ~50 modules.

  * FIFO (first-in, first-out) sells the OLDEST purchased units first, leaving the MOST RECENT purchases in
    ending inventory.
  * LIFO (last-in, first-out) sells the MOST RECENTLY purchased units first, leaving the OLDEST purchases in
    ending inventory.
  * Weighted average blends every purchase into a single average cost per unit and applies it uniformly to
    both cost of goods sold and ending inventory.
  * Regardless of method, cost of goods sold plus ending inventory value must equal EXACTLY the total cost of
    goods available for sale -- the three methods only decide how that same total cost is SPLIT, they can
    never change the total. In a period of rising purchase costs (the common real case), this split has a
    real, well-known directional consequence: FIFO reports LOWER cost of goods sold (and correspondingly
    higher gross profit) than LIFO, because it matches old, cheaper costs against current revenue, while LIFO
    reports higher cost of goods sold by matching the most recent, more expensive costs -- weighted average
    always lands between the two. This module's own test suite verifies both the universal cost-conservation
    identity and this directional property directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence


def _consume_layers(layers: Sequence[Dict[str, float]], units_to_sell: float) -> Dict[str, Any]:
    remaining_to_sell = units_to_sell
    cogs = 0.0
    ending_layers: List[Dict[str, float]] = []
    for layer in layers:
        qty, cost = layer["quantity"], layer["unit_cost"]
        if remaining_to_sell <= 1e-9:
            ending_layers.append({"quantity": qty, "unit_cost": cost})
            continue
        sold_from_layer = min(qty, remaining_to_sell)
        cogs += sold_from_layer * cost
        remaining_to_sell -= sold_from_layer
        if qty > sold_from_layer + 1e-9:
            ending_layers.append({"quantity": qty - sold_from_layer, "unit_cost": cost})
    if remaining_to_sell > 1e-6:
        raise ValueError("units_sold exceeds total units available across all purchase layers")
    ending_inventory_value = sum(l["quantity"] * l["unit_cost"] for l in ending_layers)
    return {"cogs": cogs, "ending_inventory_value": ending_inventory_value, "ending_inventory_layers": ending_layers}


def fifo(purchases: Sequence[Dict[str, float]], units_sold: float) -> Dict[str, Any]:
    """`purchases`: [{"quantity": q, "unit_cost": c}, ...] in chronological order (earliest first)."""
    return _consume_layers(purchases, units_sold)


def lifo(purchases: Sequence[Dict[str, float]], units_sold: float) -> Dict[str, Any]:
    return _consume_layers(list(reversed(purchases)), units_sold)


def weighted_average(purchases: Sequence[Dict[str, float]], units_sold: float) -> Dict[str, Any]:
    total_units = sum(p["quantity"] for p in purchases)
    total_cost = sum(p["quantity"] * p["unit_cost"] for p in purchases)
    if units_sold > total_units + 1e-6:
        raise ValueError("units_sold exceeds total units available across all purchase layers")
    average_cost_per_unit = total_cost / total_units
    return {"average_cost_per_unit": average_cost_per_unit, "cogs": units_sold * average_cost_per_unit,
            "ending_inventory_value": (total_units - units_sold) * average_cost_per_unit}


def compare_costing_methods(purchases: Sequence[Dict[str, float]], units_sold: float) -> Dict[str, Any]:
    total_cost_available = sum(p["quantity"] * p["unit_cost"] for p in purchases)
    return {"total_cost_available": total_cost_available, "fifo": fifo(purchases, units_sold),
            "lifo": lifo(purchases, units_sold), "weighted_average": weighted_average(purchases, units_sold)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "fifo" in d:
        out["fifo"] = fifo(**d["fifo"])
    if "lifo" in d:
        out["lifo"] = lifo(**d["lifo"])
    if "weighted_average" in d:
        out["weighted_average"] = weighted_average(**d["weighted_average"])
    if "compare_costing_methods" in d:
        out["compare_costing_methods"] = compare_costing_methods(**d["compare_costing_methods"])
    return out
