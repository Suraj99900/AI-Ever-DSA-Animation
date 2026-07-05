"""
AI-EVER visualizer.analysis.metrics — Code Metrics Calculator.

Calculates lines of code, blank lines, comments, cyclomatic complexity, etc.
"""

from __future__ import annotations

import ast
from typing import Any


class MetricsVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = 0
        self.classes = 0
        self.imports = 0
        self.variables = set()
        self.cyclomatic_complexity = 1  # Base complexity is 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.functions += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        self.imports += len(node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.imports += len(node.names)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.variables.add(node.id)
        self.generic_visit(node)

    # Cyclomatic Complexity checks
    def visit_If(self, node: ast.If):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)
        
    def visit_BoolOp(self, node: ast.BoolOp):
        # n-1 boolean operators
        self.cyclomatic_complexity += len(node.values) - 1
        self.generic_visit(node)


def calculate_metrics(code: str) -> dict[str, Any]:
    """Calculate code metrics from source."""
    lines = code.splitlines()
    total_lines = len(lines)
    blank_lines = len([l for l in lines if not l.strip()])
    # Simplistic comment counting
    comments = len([l for l in lines if l.strip().startswith("#")])
    
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    visitor = MetricsVisitor()
    visitor.visit(tree)

    return {
        "ok": True,
        "metrics": {
            "total_lines": total_lines,
            "blank_lines": blank_lines,
            "comments": comments,
            "code_lines": total_lines - blank_lines - comments,
            "functions": visitor.functions,
            "classes": visitor.classes,
            "imports": visitor.imports,
            "variables": len(visitor.variables),
            "cyclomatic_complexity": visitor.cyclomatic_complexity,
        }
    }
