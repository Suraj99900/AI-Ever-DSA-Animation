"""
AI-EVER visualizer.ast_builder — AST tree serialization for the AST viewer.

Parses source into a nested, JSON-safe tree the frontend renders as a
collapsible node view. No execution — safe for arbitrary code.
"""

from __future__ import annotations

import ast
from typing import Any

_MAX_DEPTH = 25
_LABEL_FIELDS = ("id", "name", "arg", "attr", "module")


def _node_label(node: ast.AST) -> str:
    """Human-friendly extra info: names, constant values, operators."""
    parts: list[str] = []
    for field in _LABEL_FIELDS:
        value = getattr(node, field, None)
        if isinstance(value, str):
            parts.append(value)
    if isinstance(node, ast.Constant):
        parts.append(repr(node.value)[:40])
    if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare)):
        op = getattr(node, "op", None) or (getattr(node, "ops", None) or [None])[0]
        if op is not None:
            parts.append(type(op).__name__)
    return " ".join(parts)


def ast_to_dict(node: ast.AST, source: str, depth: int = 0, parent_id: str | None = None) -> dict[str, Any]:
    """Recursively convert an AST node into a JSON-safe dict with extended metadata."""
    if depth > _MAX_DEPTH:
        return {"type": "…", "label": "max depth", "children": []}

    node_id = str(id(node))
    children: list[dict[str, Any]] = []

    for field, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            child = ast_to_dict(value, source, depth + 1, node_id)
            child["field"] = field
            children.append(child)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    child = ast_to_dict(item, source, depth + 1, node_id)
                    child["field"] = field
                    children.append(child)

    source_code = None
    try:
        source_code = ast.get_source_segment(source, node)
    except Exception:
        pass

    return {
        "id": node_id,
        "parent": parent_id,
        "type": type(node).__name__,
        "label": _node_label(node),
        "line": getattr(node, "lineno", None),
        "column": getattr(node, "col_offset", None),
        "source": source_code,
        "children": children,
    }


def build_ast(code: str) -> dict[str, Any]:
    """Parse code → AST tree JSON (or a syntax error report)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }
    return {"ok": True, "tree": ast_to_dict(tree, code)}
