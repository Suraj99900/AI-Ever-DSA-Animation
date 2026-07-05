"""
AI-EVER visualizer.executor — execution orchestrator.

Single entry point used by the API: traces the code, annotates every
step with explanations/complexity, and attaches the analysis summary
and call graph. Never executes code without the tracer's guards.
"""

from __future__ import annotations

from typing import Any

from visualizer.animation import annotate_steps
from visualizer.graph_builder import build_call_graph
from visualizer.parser import CodeAnalyzer
from visualizer.tracer import ExecutionTracer
from visualizer.visualization.base.visualization_manager import VisualizationManager
from visualizer.visualization.array.array_visualizer import ArrayVisualizer
from visualizer.visualization.linked_list.ll_visualizer import LinkedListVisualizer
from visualizer.visualization.tree.tree_visualizer import TreeVisualizer
from visualizer.algorithms.detector import detect_algorithm
from visualizer.algorithms.stats import calculate_live_statistics
from visualizer.algorithms.learning import generate_explanations, generate_pseudocode


class CodeExecutor:
    """Trace + analyze user code into one frontend-ready payload."""

    def __init__(self, max_steps: int = 3000, timeout_sec: float = 10.0) -> None:
        self.tracer = ExecutionTracer(max_steps=max_steps, timeout_sec=timeout_sec)
        self.analyzer = CodeAnalyzer()

    def run(self, code: str) -> dict[str, Any]:
        result = self.tracer.run(code)
        if not result["ok"]:
            return result

        analysis = self.analyzer.analyze(code)
        if analysis.get("ok"):
            annotate_steps(result["steps"], analysis["lines"])
            result["analysis"] = analysis["summary"]
            result["line_info"] = analysis["lines"]
        result["call_graph"] = build_call_graph(result["steps"])
        
        # Phase 4: Run Visualization Manager
        viz_manager = VisualizationManager()
        viz_manager.register_visualizer(ArrayVisualizer(viz_manager.dispatcher))
        viz_manager.register_visualizer(LinkedListVisualizer(viz_manager.dispatcher))
        viz_manager.register_visualizer(TreeVisualizer(viz_manager.dispatcher))
        viz_manager.process_timeline(result["steps"])
        
        # Phase 5: Run Algorithm Detection & Stats
        result["algorithm"] = detect_algorithm(code)
        result["stats"] = calculate_live_statistics(code, result["steps"])
        result["pseudocode"] = generate_pseudocode(code)
        generate_explanations(code, result["steps"])
        
        return result
