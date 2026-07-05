"""
AI-EVER visualizer.visualization.base.visualization_manager — Visualization Manager

Coordinates execution steps with visualizers to generate an event timeline.
"""

from __future__ import annotations
from typing import Any, Dict, List

from .event_dispatcher import EventDispatcher
from .base_visualizer import BaseVisualizer

class VisualizationManager:
    def __init__(self):
        self.dispatcher = EventDispatcher()
        self.visualizers: List[BaseVisualizer] = []
        
    def register_visualizer(self, visualizer: BaseVisualizer):
        self.visualizers.append(visualizer)

    def process_timeline(self, steps: List[Dict[str, Any]]) -> None:
        """
        Iterates over the execution steps provided by the tracer, 
        running them through registered visualizers to attach animation events.
        """
        for step in steps:
            for visualizer in self.visualizers:
                visualizer.process_step(step)
            
            # Flush generated events into this step
            step["animation_events"] = self.dispatcher.flush()
