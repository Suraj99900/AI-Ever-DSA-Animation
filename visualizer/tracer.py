"""
AI-EVER visualizer.tracer — line-by-line execution tracing engine.

Uses sys.settrace() to capture every executed line of user code:
current line, variables, call stack, function calls/returns,
exceptions and stdout — as a list of JSON-serializable steps
the frontend animates like a debugger.

User code is compiled to a synthetic filename so the tracer only
records user frames (never library/internal frames). Execution is
guarded by a step cap and a wall-clock timeout.
"""

from __future__ import annotations

import io
import sys
import time
import traceback
from typing import Any, Callable, Optional

from visualizer.memory import safe_repr, snapshot_vars, snapshot_values

USER_FILENAME = "<aiever>"


class ExecutionTracer:
    """Trace user Python code and produce an animated-step timeline."""

    def __init__(
        self,
        max_steps: int = 3000,
        timeout_sec: float = 10.0,
        repr_limit: int = 120,
    ) -> None:
        self.max_steps = max_steps
        self.timeout_sec = timeout_sec
        self.repr_limit = repr_limit

    # ------------------------------------------------------------------
    def run(self, code: str) -> dict:
        """Execute *code* under trace and return the full step timeline."""
        try:
            compiled = compile(code, USER_FILENAME, "exec")
        except SyntaxError as exc:
            return {
                "ok": False,
                "error": {
                    "type": "SyntaxError",
                    "message": str(exc.msg),
                    "line": exc.lineno or 1,
                    "traceback": f"SyntaxError: {exc.msg} (line {exc.lineno})",
                },
            }

        steps: list[dict] = []
        stdout_buffer = io.StringIO()
        start_time = time.monotonic()
        limit_reason: list[str] = []

        def trace(frame, event: str, arg: Any) -> Optional[Callable]:
            if frame.f_code.co_filename != USER_FILENAME:
                return None
            if time.monotonic() - start_time > self.timeout_sec:
                limit_reason.append(f"Timeout: exceeded {self.timeout_sec}s")
                raise TimeoutError(limit_reason[0])
            if len(steps) >= self.max_steps:
                limit_reason.append(f"Step limit reached ({self.max_steps} steps)")
                raise RuntimeError(limit_reason[0])
            if event in ("call", "line", "return", "exception"):
                steps.append(self._build_step(frame, event, arg, len(steps), stdout_buffer))
            return trace

        def _input_stub(prompt: str = "") -> str:
            stdout_buffer.write(f"{prompt}[input() is not supported yet]\n")
            return ""

        user_globals: dict[str, Any] = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
            "input": _input_stub,
        }

        error: Optional[dict] = None
        real_stdout = sys.stdout
        sys.stdout = stdout_buffer
        sys.settrace(trace)
        try:
            exec(compiled, user_globals)  # noqa: S102 — guarded by settrace/caps
        except BaseException as exc:
            tb_lines = traceback.format_exception_only(type(exc), exc)
            error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "line": self._find_error_line(exc),
                "traceback": "".join(tb_lines).strip(),
            }
        finally:
            sys.settrace(None)
            sys.stdout = real_stdout

        return {
            "ok": True,
            "steps": steps,
            "stdout": stdout_buffer.getvalue(),
            "error": error,
            "aborted": limit_reason[0] if limit_reason else None,
            "step_count": len(steps),
        }

    # ------------------------------------------------------------------
    def _build_step(
        self, frame, event: str, arg: Any, index: int, buffer: io.StringIO
    ) -> dict:
        """Serialize one trace event into a JSON-safe step."""
        stack: list[dict] = []
        f = frame
        while f is not None and f.f_code.co_filename == USER_FILENAME:
            name = f.f_code.co_name
            stack.append(
                {
                    "func": "main()" if name == "<module>" else f"{name}()",
                    "line": f.f_lineno,
                }
            )
            f = f.f_back
        stack.reverse()

        step: dict = {
            "i": index,
            "event": event,
            "line": frame.f_lineno,
            "func": frame.f_code.co_name,
            "stack": stack,
            "locals": snapshot_vars(frame.f_locals),
            "values": snapshot_values(frame.f_locals),
            "out": buffer.tell(),
        }
        if event == "return":
            step["ret"] = safe_repr(arg, self.repr_limit)
        if event == "exception" and arg:
            step["exc"] = {"type": arg[0].__name__, "message": str(arg[1])}
        return step

    @staticmethod
    def _find_error_line(exc: BaseException) -> int:
        """Last user-code line in the traceback (best effort)."""
        line = 1
        for tb_frame in traceback.extract_tb(exc.__traceback__):
            if tb_frame.filename == USER_FILENAME:
                line = tb_frame.lineno or line
        return line
