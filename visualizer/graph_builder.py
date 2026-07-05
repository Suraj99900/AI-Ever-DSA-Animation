"""
AI-EVER visualizer.graph_builder — call graph from the execution trace.

Builds a small caller → callee graph (with call counts) from the traced
steps, shown in the Explain tab and reusable for future graph views.
"""

from __future__ import annotations

from typing import Any


def build_call_graph(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate call events into nodes and weighted edges."""
    nodes: set[str] = set()
    edges: dict[tuple[str, str], int] = {}

    for step in steps:
        stack = step.get("stack") or []
        for frame in stack:
            nodes.add(frame["func"])
        if step.get("event") == "call" and len(stack) >= 2:
            pair = (stack[-2]["func"], stack[-1]["func"])
            edges[pair] = edges.get(pair, 0) + 1

    return {
        "nodes": sorted(nodes),
        "edges": [
            {"from": a, "to": b, "count": c}
            for (a, b), c in sorted(edges.items(), key=lambda e: -e[1])
        ],
    }
