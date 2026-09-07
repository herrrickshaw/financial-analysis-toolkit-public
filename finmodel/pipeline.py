"""A minimal declarative pipeline for chaining this toolkit's own module functions together: each step hands
a JSON-shaped input dict to one module's `from_dict()` (the same entry point every module already exposes
for its own CLI command), and later steps can reference any earlier step's OUTPUT via a
`${step_name.path.to.value}` placeholder -- the same idea behind a CI/CD pipeline's job outputs or an
Airflow DAG's XCom, scoped down to this toolkit's own ~40 modules rather than a general workflow engine.

A step is `{"name": str, "module": str, "inputs": dict}`, where `module` is any finmodel module exposing
`from_dict(d) -> dict` (every engine in this toolkit does). Steps execute strictly in the given list order --
this is a PIPELINE, not a dependency graph -- so a step referencing `${x...}` must come after the step named
`x`. A placeholder must be a step input's ENTIRE string value, of the form `${step_name.key1.key2.3.key4}`;
dotted segments that parse as an integer index into a list, otherwise they look up a dict key. Only
whole-string placeholders are substituted (so a referenced number stays a number rather than getting
stringified into a template) -- embedding a placeholder inside a longer string is not supported, since these
values are numbers and structured results, not text to interpolate into a sentence.
"""
from __future__ import annotations

import importlib
import re
from typing import Any, Dict, List

_PLACEHOLDER = re.compile(r"^\$\{([\w.]+)\}$")


def _get_path(root: Dict[str, Any], path: str) -> Any:
    node: Any = root
    for segment in path.split("."):
        if isinstance(node, list):
            node = node[int(segment)]
        elif isinstance(node, dict):
            if segment not in node:
                raise KeyError(f"'{segment}' not found while resolving '{path}'")
            node = node[segment]
        else:
            raise KeyError(f"cannot descend into '{segment}' of a {type(node).__name__} while resolving '{path}'")
    return node


def _resolve(value: Any, results: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        m = _PLACEHOLDER.match(value)
        return _get_path(results, m.group(1)) if m else value
    if isinstance(value, dict):
        return {k: _resolve(v, results) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, results) for v in value]
    return value


def run_pipeline(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    order: List[str] = []
    for step in steps:
        name = step["name"]
        module_name = step["module"]
        if name in results:
            raise ValueError(f"duplicate step name: {name}")
        module = importlib.import_module(f"finmodel.{module_name}")
        if not hasattr(module, "from_dict"):
            raise ValueError(f"module '{module_name}' has no from_dict() entry point")
        resolved_inputs = _resolve(step.get("inputs", {}), results)
        results[name] = module.from_dict(resolved_inputs)
        order.append(name)
    return {"order": order, "steps": results}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return run_pipeline(d["steps"])
