"""
AI-EVER visualizer.memory — variable & heap snapshot builders.

Converts live frame variables into two parallel views:
    snapshot_vars()   — safe reprs for the Memory panel
    snapshot_values() — JSON-safe structures the frontend can DRAW
"""

from __future__ import annotations

import types
from typing import Any

# Values never shown in the memory panel
HIDDEN_TYPES = (
    types.ModuleType,
    types.FunctionType,
    types.BuiltinFunctionType,
    types.MethodType,
    type,
)


def safe_repr(value: Any, limit: int = 120) -> str:
    """repr() that never raises and never explodes in size."""
    try:
        text = repr(value)
    except Exception:
        text = f"<unrepresentable {type(value).__name__}>"
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def snapshot_vars(frame_vars: dict) -> dict[str, str]:
    """Serialize a frame's variables (skip dunders, modules, functions)."""
    out: dict[str, str] = {}
    for name, value in frame_vars.items():
        if name.startswith("__"):
            continue
        if isinstance(value, HIDDEN_TYPES):
            continue
        out[name] = safe_repr(value)
    return out


def json_safe(value: Any, depth: int = 0, max_items: int = 64) -> Any:
    """Convert a value to a JSON-safe structure the frontend can draw.

    Returns None for values that cannot be visualized (objects, frames…).
    Guards against deep nesting, huge containers and non-finite floats.
    """
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value if abs(value) < 10**15 else None
    if isinstance(value, float):
        return value if value == value and abs(value) != float("inf") else None
    if isinstance(value, str):
        return value[:200]
    if depth >= 4:
        return None
    if isinstance(value, (list, tuple)):
        return [json_safe(v, depth + 1) for v in list(value)[:max_items]]
    if isinstance(value, (set, frozenset)):
        try:
            items = sorted(value)
        except TypeError:
            items = list(value)
        return {"__set__": [json_safe(v, depth + 1) for v in items[:max_items]]}
    if isinstance(value, dict):
        return {
            str(k)[:50]: json_safe(v, depth + 1)
            for k, v in list(value.items())[:max_items]
        }
    if hasattr(value, "__dict__"):
        # Custom object serialization (up to depth 2)
        obj_dict = {"__class__": type(value).__name__, "__id__": id(value)}
        for k, v in list(value.__dict__.items())[:max_items]:
            if not k.startswith("__"):
                # We need deeper depth for objects to see node.next or node.left
                # So we pass depth instead of depth+1 for the first level or allow up to depth 3
                obj_dict[k] = json_safe(v, depth + 1, max_items) if depth < 3 else id(v)
        return obj_dict
        
    return None


def snapshot_values(frame_vars: dict) -> dict[str, Any]:
    """Structured (drawable) values for the visualization panel."""
    out: dict[str, Any] = {}
    for name, value in frame_vars.items():
        if name.startswith("__") or isinstance(value, HIDDEN_TYPES):
            continue
        safe = json_safe(value)
        if safe is not None:
            out[name] = safe
    return out
