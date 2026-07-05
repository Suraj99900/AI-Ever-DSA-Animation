"""
AI-EVER visualizer.visualization.base.base_visualizer — Base Visualizer

Abstract base class for all Data Structure visualizers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from .event_dispatcher import EventDispatcher

class BaseVisualizer(ABC):
    def __init__(self, name: str, dispatcher: EventDispatcher):
        self.name = name
        self.dispatcher = dispatcher
        self.state: Any = None

    @abstractmethod
    def process_step(self, step_data: Dict[str, Any]) -> None:
        """
        Processes a single execution step and its locals to detect 
        if this data structure changed, generating events via dispatcher.
        """
        pass
