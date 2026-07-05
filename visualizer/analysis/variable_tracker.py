"""
AI-EVER visualizer.analysis.variable_tracker — Variable Lifetime and Smell Detector.

Tracks variables through their lifecycle and detects unused variables and magic numbers.
"""

from __future__ import annotations

import ast
from typing import Any


class VariableTracker(ast.NodeVisitor):
    def __init__(self):
        self.variables: dict[str, dict[str, Any]] = {}
        self.magic_numbers: list[dict[str, Any]] = []

    def _track(self, name: str, action: str, line: int | None):
        if not line:
            return
            
        if name not in self.variables:
            self.variables[name] = {
                "name": name,
                "birth": line,
                "reads": [],
                "updates": [],
                "death": None,
                "unused": True
            }
            
        if action == "read":
            self.variables[name]["reads"].append(line)
            self.variables[name]["unused"] = False
        elif action == "update":
            if line != self.variables[name]["birth"]:
                self.variables[name]["updates"].append(line)
        elif action == "delete":
            self.variables[name]["death"] = line

    def visit_Name(self, node: ast.Name):
        action = "read"
        if isinstance(node.ctx, ast.Store):
            action = "update"
        elif isinstance(node.ctx, ast.Del):
            action = "delete"
            
        self._track(node.id, action, getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg):
        self._track(node.arg, "update", getattr(node, "lineno", None))
        self.generic_visit(node)
        
    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)) and node.value not in (0, 1, -1, 2):
            self.magic_numbers.append({
                "value": node.value,
                "line": getattr(node, "lineno", None)
            })
        self.generic_visit(node)


def analyze_variables(code: str) -> dict[str, Any]:
    """Parse code → Variable Lifetimes JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    tracker = VariableTracker()
    tracker.visit(tree)
    
    unused_vars = [v["name"] for v in tracker.variables.values() if v["unused"]]

    return {
        "ok": True,
        "variables": list(tracker.variables.values()),
        "smells": {
            "unused_variables": unused_vars,
            "magic_numbers": tracker.magic_numbers
        }
    }
