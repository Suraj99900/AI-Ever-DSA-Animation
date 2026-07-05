"""
AI-EVER visualizer.analysis.cfg_builder — Control Flow Graph Generator.

Generates a basic Control Flow Graph (CFG) from Python source code.
Nodes represent basic blocks or individual statements.
Edges represent the control flow between them.
"""

from __future__ import annotations

import ast
from typing import Any


class CFGNode:
    def __init__(self, id: str, label: str, line: int | None = None):
        self.id = id
        self.label = label
        self.line = line
        self.next: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "line": self.line,
            "next": self.next,
        }


class CFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.nodes: dict[str, CFGNode] = {}
        self.edges: list[dict[str, str]] = []
        self._counter = 0
        self.current_block: str | None = None

    def _next_id(self) -> str:
        self._counter += 1
        return f"node_{self._counter}"

    def add_node(self, label: str, line: int | None = None) -> str:
        nid = self._next_id()
        self.nodes[nid] = CFGNode(nid, label, line)
        if self.current_block:
            self.add_edge(self.current_block, nid)
        self.current_block = nid
        return nid

    def add_edge(self, source: str, target: str, label: str = ""):
        self.nodes[source].next.append(target)
        self.edges.append({"source": source, "target": target, "label": label})

    def build(self, tree: ast.AST) -> dict[str, Any]:
        self.add_node("Start")
        self.visit(tree)
        end_node = self._next_id()
        self.nodes[end_node] = CFGNode(end_node, "End")
        if self.current_block:
            self.add_edge(self.current_block, end_node)
        
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": self.edges,
        }

    # Visitors for basic statements
    def visit_Assign(self, node: ast.Assign):
        self.add_node("Assign", getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr):
        self.add_node("Expr", getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        self.add_node("Return", getattr(node, "lineno", None))
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        if_node = self.add_node("If condition", getattr(node, "lineno", None))
        
        # True branch
        self.current_block = if_node
        for stmt in node.body:
            self.visit(stmt)
        end_true = self.current_block
        
        # False branch
        self.current_block = if_node
        for stmt in node.orelse:
            self.visit(stmt)
        end_false = self.current_block
        
        # Merge point
        merge_node = self._next_id()
        self.nodes[merge_node] = CFGNode(merge_node, "End If")
        if end_true:
            self.add_edge(end_true, merge_node)
        if end_false:
            self.add_edge(end_false, merge_node)
            
        self.current_block = merge_node

    def visit_While(self, node: ast.While):
        while_node = self.add_node("While condition", getattr(node, "lineno", None))
        
        # Body
        self.current_block = while_node
        for stmt in node.body:
            self.visit(stmt)
        
        # Loop back
        if self.current_block:
            self.add_edge(self.current_block, while_node)
            
        # Exit
        exit_node = self._next_id()
        self.nodes[exit_node] = CFGNode(exit_node, "End While")
        self.add_edge(while_node, exit_node)
        
        self.current_block = exit_node

    def visit_For(self, node: ast.For):
        for_node = self.add_node("For loop", getattr(node, "lineno", None))
        
        # Body
        self.current_block = for_node
        for stmt in node.body:
            self.visit(stmt)
            
        # Loop back
        if self.current_block:
            self.add_edge(self.current_block, for_node)
            
        # Exit
        exit_node = self._next_id()
        self.nodes[exit_node] = CFGNode(exit_node, "End For")
        self.add_edge(for_node, exit_node)
        
        self.current_block = exit_node


def build_cfg(code: str) -> dict[str, Any]:
    """Parse code → Control Flow Graph JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    
    builder = CFGBuilder()
    cfg_data = builder.build(tree)
    return {"ok": True, "cfg": cfg_data}
