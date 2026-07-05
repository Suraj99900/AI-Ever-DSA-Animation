"""
AI-EVER visualizer.algorithms.stats — Live Statistics Tracker.

Tracks swaps, comparisons, and iterations based on the AST and execution trace.
"""

from __future__ import annotations
import ast
from typing import Any

class OperationTracker(ast.NodeVisitor):
    def __init__(self):
        self.comparison_lines = set()
        self.swap_lines = set()

    def visit_Compare(self, node: ast.Compare):
        self.comparison_lines.add(node.lineno)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # Swap via tuple packing: a, b = b, a
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            self.swap_lines.add(node.lineno)
        self.generic_visit(node)


def calculate_live_statistics(code: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    tracker = OperationTracker()
    try:
        tree = ast.parse(code)
        tracker.visit(tree)
    except Exception:
        pass
        
    stats = {
        "comparisons": 0,
        "swaps": 0,
        "total_steps": len(steps)
    }
    
    # We will inject these running totals into the steps themselves so the frontend can animate them!
    running_comparisons = 0
    running_swaps = 0
    
    for step in steps:
        line = step.get("line")
        if line in tracker.comparison_lines:
            running_comparisons += 1
        if line in tracker.swap_lines:
            running_swaps += 1
            
        step["stats"] = {
            "comparisons": running_comparisons,
            "swaps": running_swaps
        }
        
    stats["comparisons"] = running_comparisons
    stats["swaps"] = running_swaps
    return stats
