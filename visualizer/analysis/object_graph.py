"""
AI-EVER visualizer.analysis.object_graph — Object Graph Generator.

Statically detects instantiations of classes to approximate an object reference graph.
"""

from __future__ import annotations

import ast
from typing import Any
from .class_diagram import build_class_diagram


class ObjectGraphBuilder(ast.NodeVisitor):
    def __init__(self, known_classes: set[str]):
        self.known_classes = known_classes
        self.objects: dict[str, dict[str, Any]] = {}
        self.references: list[dict[str, str]] = []

    def visit_Assign(self, node: ast.Assign):
        # Check if right side is a call to a known class (instantiation)
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            class_name = node.value.func.id
            # Best-effort static matching
            if class_name in self.known_classes:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        obj_name = target.id
                        self.objects[obj_name] = {
                            "id": obj_name,
                            "type": class_name,
                            "line": getattr(node, "lineno", None)
                        }
        
        # Check if right side is a reference to a known object
        elif isinstance(node.value, ast.Name):
            source_obj = node.value.id
            if source_obj in self.objects:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_obj = target.id
                        self.references.append({
                            "source": target_obj,
                            "target": source_obj,
                            "type": "alias"
                        })
        self.generic_visit(node)


def build_object_graph(code: str) -> dict[str, Any]:
    """Parse code → Object Graph JSON (best effort static analysis)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    # First pass: find known classes
    class_diagram_res = build_class_diagram(code)
    known_classes = set()
    if class_diagram_res.get("ok"):
        known_classes = {c["id"] for c in class_diagram_res["class_diagram"]["nodes"]}

    builder = ObjectGraphBuilder(known_classes)
    builder.visit(tree)
    
    return {
        "ok": True,
        "object_graph": {
            "nodes": list(builder.objects.values()),
            "edges": builder.references
        }
    }
