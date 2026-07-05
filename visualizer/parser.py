"""
AI-EVER visualizer.parser — AST-based code analysis.

Produces, for every source line:
    - a plain-English explanation of what the line does
    - a per-line time complexity (O(1), O(n)…)
and an overall ESTIMATED time/space complexity summary derived from
loop nesting, halving patterns, container building and recursion.
"""

from __future__ import annotations

import ast
from typing import Any

_MAX_TEXT = 70


def _src(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        text = " ".join(ast.unparse(node).split())
    except Exception:
        text = type(node).__name__
    return text[: _MAX_TEXT - 1] + "…" if len(text) > _MAX_TEXT else text


def _is_halving(loop: ast.While | ast.For) -> bool:
    """Does the loop body shrink its range by division/doubling? → O(log n)"""
    try:
        body_src = ast.unparse(loop)
    except Exception:
        return False
    return any(p in body_src for p in ("// 2", "//2", "/ 2", "* 2", ">> 1", "<< 1"))


def _builds_container(node: ast.AST) -> bool:
    """Does this statement allocate a growing container? (space heuristic)"""
    for sub in ast.walk(node):
        if isinstance(sub, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            return True
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
            if sub.func.id in ("list", "dict", "set", "sorted"):
                return True
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
            if sub.func.attr in ("append", "extend", "insert", "add", "update"):
                return True
    return False


class CodeAnalyzer:
    """Static analysis: explanations + complexity estimates."""

    def analyze(self, code: str) -> dict[str, Any]:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {"ok": False, "error": {"type": "SyntaxError", "line": exc.lineno or 1}}

        self.lines: dict[int, dict[str, str]] = {}
        self.func_names: set[str] = {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.recursive = self._find_recursion(tree)
        self.allocates = False

        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.stmt):
                self._explain(stmt)
            if isinstance(stmt, ast.stmt) and _builds_container(stmt):
                self.allocates = True

        chain = self._max_loop_chain(tree.body)
        return {
            "ok": True,
            "lines": {str(k): v for k, v in self.lines.items()},
            "summary": {
                "time": self._chain_to_big_o(chain),
                "space": self._space_estimate(),
                "loops": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))),
                "functions": sorted(self.func_names),
                "recursive": sorted(self.recursive),
                "note": "Estimated statically from loop nesting, halving patterns and allocations.",
            },
        }

    # ---------------- per-line explanations ----------------
    def _put(self, node: ast.stmt, explain: str, cx: str = "O(1)") -> None:
        line = getattr(node, "lineno", None)
        if line and line not in self.lines:
            self.lines[line] = {"explain": explain, "cx": cx}

    def _explain(self, s: ast.stmt) -> None:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ", ".join(a.arg for a in s.args.args)
            self._put(s, f"Define function {s.name}({args}) — body runs only when called.")
        elif isinstance(s, ast.ClassDef):
            self._put(s, f"Define class {s.name} — a blueprint for objects.")
        elif isinstance(s, ast.Assign):
            target = ", ".join(_src(t) for t in s.targets)
            value = _src(s.value)
            if "// 2" in value or "//2" in value:
                self._put(s, f"Calculate {target} = {value} — find the middle index to split the range into two halves.")
            elif isinstance(s.value, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
                self._put(s, f"Create {target} with initial value {value}.",
                          "O(n)" if _builds_container(s) else "O(1)")
            else:
                self._put(s, f"Assign {target} = {value}.",
                          "O(n)" if _builds_container(s) else "O(1)")
        elif isinstance(s, ast.AugAssign):
            self._put(s, f"Update {_src(s.target)} using {type(s.op).__name__} with {_src(s.value)}.")
        elif isinstance(s, ast.While):
            cx = "O(log n)" if _is_halving(s) else "O(n)"
            extra = " Each pass halves the search space." if cx == "O(log n)" else ""
            self._put(s, f"Loop while {_src(s.test)} holds — condition is re-checked every iteration.{extra}", cx)
        elif isinstance(s, ast.For):
            self._put(s, f"Iterate {_src(s.target)} over {_src(s.iter)} — one pass per element.", "O(n)")
        elif isinstance(s, ast.If):
            self._put(s, f"Check whether {_src(s.test)} — choose which branch to execute.")
        elif isinstance(s, ast.Return):
            self._put(s, f"Return {_src(s.value) or 'None'} to the caller and pop this frame off the stack.")
        elif isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
            fn = s.value.func
            fname = fn.id if isinstance(fn, ast.Name) else _src(fn)
            if fname == "print":
                self._put(s, "Print output to the console.")
            elif fname in self.func_names:
                self._put(s, f"Call {fname}(…) — push a new frame onto the call stack.")
            else:
                self._put(s, f"Call {fname}(…).")
        elif isinstance(s, ast.Break):
            self._put(s, "Break — exit the enclosing loop immediately.")
        elif isinstance(s, ast.Continue):
            self._put(s, "Continue — skip to the next loop iteration.")
        elif isinstance(s, (ast.Import, ast.ImportFrom)):
            self._put(s, f"Import: {_src(s)}.")
        elif isinstance(s, ast.Raise):
            self._put(s, f"Raise an exception: {_src(s.exc) or ''}.")
        elif isinstance(s, ast.Try):
            self._put(s, "Try block — run statements and catch matching exceptions.")
        else:
            self._put(s, f"Execute: {_src(s)}.")

    # ---------------- overall complexity ----------------
    def _max_loop_chain(self, stmts: list[ast.stmt]) -> list[str]:
        """Longest nested-loop chain, each element 'n' or 'log'."""
        best: list[str] = []

        def weight(chain: list[str]) -> tuple:
            return (len(chain), sum(1 for c in chain if c == "n"))

        for s in stmts:
            chain: list[str] = []
            if isinstance(s, (ast.For, ast.While)):
                factor = "log" if _is_halving(s) else "n"
                chain = [factor] + self._max_loop_chain(s.body)
            elif isinstance(s, ast.If):
                chain = max(
                    self._max_loop_chain(s.body),
                    self._max_loop_chain(s.orelse),
                    key=weight,
                )
            elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Try, ast.With)):
                chain = self._max_loop_chain(getattr(s, "body", []))
            if weight(chain) > weight(best):
                best = chain
        return best

    @staticmethod
    def _chain_to_big_o(chain: list[str]) -> str:
        if not chain:
            return "O(1)"
        n_count = chain.count("n")
        log_count = chain.count("log")
        parts = []
        if n_count == 1:
            parts.append("n")
        elif n_count > 1:
            parts.append(f"n{'²³⁴'[n_count - 2] if n_count <= 4 else f'^{n_count}'}")
        if log_count:
            parts.append("log n" if log_count == 1 else f"log{'²' if log_count == 2 else f'^{log_count}'} n")
        return f"O({' · '.join(parts)})"

    def _space_estimate(self) -> str:
        if self.recursive:
            return "O(n) — recursion uses stack frames"
        if self.allocates:
            return "O(n) — builds containers"
        return "O(1)"

    def _find_recursion(self, tree: ast.Module) -> set[str]:
        recursive: set[str] = set()
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for call in ast.walk(fn):
                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Name)
                        and call.func.id == fn.name
                    ):
                        recursive.add(fn.name)
        return recursive
