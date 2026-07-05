"""
AI-EVER visualizer.analysis.dfg_builder — Data Flow Graph Generator.

Tracks variable creation, assignment, read, write, and deletion.
"""

from __future__ import annotations

import ast
from typing import Any


class DFGNode:
    def __init__(self, id: str, var_name: str, action: str, line: int | None = None):
        self.id = id
        self.var_name = var_name
        self.action = action  # "create", "read", "write", "delete"
        self.line = line
        self.next: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "var_name": self.var_name,
            "action": self.action,
            "line": self.line,
            "next": self.next,
        }


class DFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.nodes: dict[str, DFGNode] = {}
        self.edges: list[dict[str, str]] = []
        self._counter = 0
        self.last_seen: dict[str, str] = {}  # var_name -> last node id

    def _next_id(self) -> str:
        self._counter += 1
        return f"dfg_{self._counter}"

    def add_node(self, var_name: str, action: str, line: int | None = None) -> str:
        nid = self._next_id()
        self.nodes[nid] = DFGNode(nid, var_name, action, line)
        
        # Link from the previous action on this variable
        if var_name in self.last_seen:
            prev_id = self.last_seen[var_name]
            self.nodes[prev_id].next.append(nid)
            self.edges.append({"source": prev_id, "target": nid, "label": "flow"})
            
        self.last_seen[var_name] = nid
        return nid

    def build(self, tree: ast.AST) -> dict[str, Any]:
        self.visit(tree)
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": self.edges,
        }

    def visit_Name(self, node: ast.Name):
        action = "read"
        if isinstance(node.ctx, ast.Store):
            # Check if it's creation or write
            action = "write" if node.id in self.last_seen else "create"
        elif isinstance(node.ctx, ast.Load):
            action = "read"
        elif isinstance(node.ctx, ast.Del):
            action = "delete"
            
        self.add_node(node.id, action, getattr(node, "lineno", None))
        self.generic_visit(node)
        
    def visit_arg(self, node: ast.arg):
        self.add_node(node.arg, "create", getattr(node, "lineno", None))
        self.generic_visit(node)


def build_dfg(code: str) -> dict[str, Any]:
    """Parse code → Data Flow Graph JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    
    builder = DFGBuilder()
    dfg_data = builder.build(tree)
    return {"ok": True, "dfg": dfg_data}
