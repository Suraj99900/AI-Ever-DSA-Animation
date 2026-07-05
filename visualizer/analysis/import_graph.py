"""
AI-EVER visualizer.analysis.import_graph — Import Graph Generator.

Tracks module dependencies based on Import and ImportFrom AST nodes.
"""

from __future__ import annotations

import ast
from typing import Any


class ImportGraphBuilder(ast.NodeVisitor):
    def __init__(self, module_name: str = "main"):
        self.module_name = module_name
        self.nodes: set[str] = {module_name}
        self.edges: list[dict[str, str]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.nodes.add(alias.name)
            self.edges.append({
                "source": self.module_name,
                "target": alias.name,
                "type": "import"
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.nodes.add(node.module)
            self.edges.append({
                "source": self.module_name,
                "target": node.module,
                "type": "import_from",
                "names": [alias.name for alias in node.names]
            })
        self.generic_visit(node)


def build_import_graph(code: str, module_name: str = "main") -> dict[str, Any]:
    """Parse code → Import Graph JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    
    builder = ImportGraphBuilder(module_name)
    builder.visit(tree)
    
    return {
        "ok": True,
        "import_graph": {
            "nodes": [{"id": n, "label": n} for n in sorted(list(builder.nodes))],
            "edges": builder.edges
        }
    }
