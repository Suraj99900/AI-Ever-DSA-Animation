"""
AI-EVER visualizer.flowchart — automatic flowchart generation from AST.

Builds a nested, JSON-safe flow structure (process / decision / loop /
return nodes) that the frontend renders as a structured flowchart.
Pure Python + ast — no Graphviz binary needed, fully offline.
"""

from __future__ import annotations

import ast
from typing import Any

_MAX_TEXT = 60


def _src(node: ast.AST) -> str:
    """Source text of an expression/statement (truncated)."""
    try:
        text = ast.unparse(node)
    except Exception:
        text = type(node).__name__
    text = " ".join(text.split())
    return text[: _MAX_TEXT - 1] + "…" if len(text) > _MAX_TEXT else text


def _build_node(stmt: ast.stmt) -> dict[str, Any]:
    """Convert one statement into a flow node (recursing into bodies)."""
    line = getattr(stmt, "lineno", None)

    if isinstance(stmt, ast.If):
        return {
            "type": "if",
            "cond": _src(stmt.test),
            "line": line,
            "body": _build_body(stmt.body),
            "orelse": _build_body(stmt.orelse),
        }
    if isinstance(stmt, ast.For):
        return {
            "type": "loop",
            "head": f"for {_src(stmt.target)} in {_src(stmt.iter)}",
            "line": line,
            "body": _build_body(stmt.body),
        }
    if isinstance(stmt, ast.While):
        return {
            "type": "loop",
            "head": f"while {_src(stmt.test)}",
            "line": line,
            "body": _build_body(stmt.body),
        }
    if isinstance(stmt, ast.Return):
        return {
            "type": "return",
            "text": f"return {_src(stmt.value)}" if stmt.value else "return",
            "line": line,
        }
    if isinstance(stmt, (ast.Break, ast.Continue)):
        return {"type": "return", "text": type(stmt).__name__.lower(), "line": line}
    if isinstance(stmt, ast.Try):
        return {
            "type": "loop",  # rendered as a container block
            "head": "try / except",
            "line": line,
            "body": _build_body(stmt.body)
            + [n for h in stmt.handlers for n in _build_body(h.body)],
        }
    # Any other statement → simple process box
    return {"type": "process", "text": _src(stmt), "line": line}


def _build_body(stmts: list[ast.stmt]) -> list[dict[str, Any]]:
    """Convert a statement list, skipping nested function/class defs."""
    return [
        _build_node(s)
        for s in stmts
        if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def build_flow(code: str) -> dict[str, Any]:
    """Parse code → flowchart structure per function + module main flow."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "ok": False,
            "error": {"type": "SyntaxError", "message": str(exc.msg), "line": exc.lineno or 1},
        }

    functions: list[dict[str, Any]] = []
    main: list[dict[str, Any]] = []

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": stmt.name,
                    "args": ", ".join(a.arg for a in stmt.args.args),
                    "line": stmt.lineno,
                    "body": _build_body(stmt.body),
                }
            )
        elif isinstance(stmt, ast.ClassDef):
            for sub in stmt.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(
                        {
                            "name": f"{stmt.name}.{sub.name}",
                            "args": ", ".join(a.arg for a in sub.args.args),
                            "line": sub.lineno,
                            "body": _build_body(sub.body),
                        }
                    )
        else:
            main.append(_build_node(stmt))

    return {"ok": True, "main": main, "functions": functions}
