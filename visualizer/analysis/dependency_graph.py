"""
AI-EVER visualizer.analysis.dependency_graph — Dependency Graph Generator.

Aggregates relationships between modules, functions, and classes.
"""

from __future__ import annotations

import ast
from typing import Any

from .import_graph import build_import_graph
from .call_graph import build_call_graph
from .class_diagram import build_class_diagram

def build_dependency_graph(code: str) -> dict[str, Any]:
    """Parse code → Unified Dependency Graph JSON."""
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    # Gather data from the specialized graph builders
    imports = build_import_graph(code).get("import_graph", {"nodes": [], "edges": []})
    calls = build_call_graph(code).get("call_graph", {"nodes": [], "edges": []})
    classes = build_class_diagram(code).get("class_diagram", {"nodes": [], "edges": []})

    nodes = {}
    edges = []

    # Map node types
    for n in imports["nodes"]:
        nodes[n["id"]] = {"id": n["id"], "label": n["id"], "type": "module"}
    for n in calls["nodes"]:
        if n["id"] not in nodes:
            nodes[n["id"]] = {"id": n["id"], "label": n["id"], "type": "function"}
    for n in classes["nodes"]:
        if n["id"] not in nodes:
            nodes[n["id"]] = {"id": n["id"], "label": n["id"], "type": "class"}

    # Add edges
    for e in imports["edges"]:
        edges.append({**e, "relation": "imports"})
    for e in calls["edges"]:
        edges.append({**e, "relation": "calls"})
    for e in classes["edges"]:
        edges.append({**e, "relation": "inherits"})

    return {
        "ok": True,
        "dependency_graph": {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    }
