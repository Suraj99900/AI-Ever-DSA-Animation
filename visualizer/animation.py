"""
AI-EVER visualizer.animation — step annotation for the animation stream.

Merges static analysis (explanations, per-line complexity) into the
dynamic trace steps so the frontend can show an explanation for every
executed line without a second request.
"""

from __future__ import annotations

from typing import Any

_EVENT_EXPLAIN = {
    "call": "Enter the function — a new frame is pushed onto the call stack.",
    "return": "Leave the function — its frame is popped and the value returned.",
    "exception": "An exception was raised on this line.",
}


def annotate_steps(steps: list[dict[str, Any]], line_info: dict[str, dict]) -> None:
    """Attach 'explain' and 'cx' to every step, in place."""
    for step in steps:
        info = line_info.get(str(step.get("line")))
        if info:
            step["explain"] = info["explain"]
            step["cx"] = info["cx"]
        event_note = _EVENT_EXPLAIN.get(step.get("event"))
        if event_note:
            step["explain"] = (
                f"{event_note} {step.get('explain', '')}".strip()
                if step.get("event") != "line"
                else step.get("explain", "")
            )
