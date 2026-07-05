"""
AI-EVER visualizer.analysis.complexity — Complexity Analyzer.

Detects loops, nested loops, recursion, and estimates time/space complexity.
"""

from __future__ import annotations

import ast
from typing import Any
from .call_graph import build_call_graph


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_loop_depth = 0
        self.current_loop_depth = 0
        self.has_recursion = False
        self.recursive_funcs = set()
        
        # Track function definitions to check recursion via Call Graph
        self.defined_functions = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.current_loop_depth += 1
        if self.current_loop_depth > self.max_loop_depth:
            self.max_loop_depth = self.current_loop_depth
            
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_While(self, node: ast.While):
        self.current_loop_depth += 1
        if self.current_loop_depth > self.max_loop_depth:
            self.max_loop_depth = self.current_loop_depth
            
        self.generic_visit(node)
        self.current_loop_depth -= 1


def estimate_time_complexity(max_loop_depth: int, has_recursion: bool) -> str:
    if has_recursion:
        # Simplistic assumption for standard recursion without memoization
        return "O(2^n) or O(n) (Recursion detected, bounds vary)"
    if max_loop_depth == 0:
        return "O(1) (Constant time)"
    elif max_loop_depth == 1:
        return "O(n) (Linear time)"
    elif max_loop_depth == 2:
        return "O(n^2) (Quadratic time)"
    else:
        return f"O(n^{max_loop_depth}) (Polynomial time)"


def analyze_complexity(code: str) -> dict[str, Any]:
    """Parse code → Complexity Analysis JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    
    # Check recursion using call graph
    cg_res = build_call_graph(code)
    if cg_res.get("ok"):
        edges = cg_res["call_graph"]["edges"]
        for e in edges:
            if e["source"] == e["target"] and e["source"] in visitor.defined_functions:
                visitor.has_recursion = True
                visitor.recursive_funcs.add(e["source"])
    
    time_est = estimate_time_complexity(visitor.max_loop_depth, visitor.has_recursion)
    
    return {
        "ok": True,
        "complexity": {
            "max_loop_depth": visitor.max_loop_depth,
            "has_nested_loops": visitor.max_loop_depth > 1,
            "has_recursion": visitor.has_recursion,
            "recursive_functions": list(visitor.recursive_funcs),
            "estimated_time_complexity": time_est,
            "estimated_space_complexity": "O(n) (Estimated due to recursion/arrays)" if visitor.has_recursion else "O(1) auxiliary"
        }
    }
