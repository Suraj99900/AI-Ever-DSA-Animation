"""
AI-EVER visualizer.analysis.call_graph — Call Graph Generator.

Generates a static call graph by traversing AST and finding function definitions and calls.
"""

from __future__ import annotations

import ast
from typing import Any


class CallGraphBuilder(ast.NodeVisitor):
    def __init__(self):
        self.nodes: set[str] = set()
        self.edges: list[dict[str, str | int]] = []
        self.current_func: str = "main"
        self.nodes.add("main")

    def _get_call_name(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev_func = self.current_func
        self.current_func = node.name
        self.nodes.add(node.name)
        
        self.generic_visit(node)
        
        self.current_func = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        prev_func = self.current_func
        self.current_func = node.name
        self.nodes.add(node.name)
        
        self.generic_visit(node)
        
        self.current_func = prev_func

    def visit_Call(self, node: ast.Call):
        call_name = self._get_call_name(node)
        if call_name:
            self.nodes.add(call_name)
            # Check if edge already exists, increment count
            existing = None
            for e in self.edges:
                if e["source"] == self.current_func and e["target"] == call_name:
                    existing = e
                    break
            
            if existing:
                existing["count"] = int(existing.get("count", 0)) + 1
            else:
                self.edges.append({
                    "source": self.current_func,
                    "target": call_name,
                    "count": 1,
                    "line": getattr(node, "lineno", None)
                })

        self.generic_visit(node)


def build_call_graph(code: str) -> dict[str, Any]:
    """Parse code → Call Graph JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    
    builder = CallGraphBuilder()
    builder.visit(tree)
    
    return {
        "ok": True,
        "call_graph": {
            "nodes": [{"id": n, "label": n} for n in sorted(list(builder.nodes))],
            "edges": builder.edges
        }
    }
