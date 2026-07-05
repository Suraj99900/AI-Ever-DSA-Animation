"""
AI-EVER visualizer.analysis.class_diagram — Class Diagram Generator.

Generates a class hierarchy and property diagram based on AST.
"""

from __future__ import annotations

import ast
from typing import Any


class ClassDiagramBuilder(ast.NodeVisitor):
    def __init__(self):
        self.classes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, str]] = []
        self.current_class: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        self.classes[class_name] = {
            "id": class_name,
            "label": class_name,
            "methods": [],
            "properties": []
        }
        
        # Track inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.edges.append({
                    "source": class_name,
                    "target": base.id,
                    "type": "inheritance"
                })
            elif isinstance(base, ast.Attribute):
                self.edges.append({
                    "source": class_name,
                    "target": base.attr,
                    "type": "inheritance"
                })

        prev_class = self.current_class
        self.current_class = class_name
        
        self.generic_visit(node)
        
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class:
            self.classes[self.current_class]["methods"].append(node.name)
        # Skip nested functions inside methods
        
    def visit_Assign(self, node: ast.Assign):
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    if target.attr not in self.classes[self.current_class]["properties"]:
                        self.classes[self.current_class]["properties"].append(target.attr)
        self.generic_visit(node)


def build_class_diagram(code: str) -> dict[str, Any]:
    """Parse code → Class Diagram JSON."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    
    builder = ClassDiagramBuilder()
    builder.visit(tree)
    
    return {
        "ok": True,
        "class_diagram": {
            "nodes": list(builder.classes.values()),
            "edges": builder.edges
        }
    }
