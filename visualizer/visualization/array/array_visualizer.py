"""
AI-EVER visualizer.visualization.array.array_visualizer — Array Visualizer

Detects changes to arrays (lists) and generates animation events.
"""

from __future__ import annotations
from typing import Any, Dict
from ..base.base_visualizer import BaseVisualizer

class ArrayVisualizer(BaseVisualizer):
    def __init__(self, dispatcher):
        super().__init__("ArrayVisualizer", dispatcher)
        self.state: Dict[str, list] = {}

    def process_step(self, step_data: Dict[str, Any]) -> None:
        values = step_data.get("values", {})
        
        # We need to detect newly created lists, updated lists, or deleted lists
        current_arrays = {}
        for var_name, value in values.items():
            if isinstance(value, list):
                current_arrays[var_name] = value

        # Detect creations and updates
        for var_name, current_val in current_arrays.items():
            if var_name not in self.state:
                # Created
                self.dispatcher.dispatch(
                    event_type="ArrayCreated",
                    source=var_name,
                    metadata={"value": current_val}
                )
            else:
                # Compare to detect updates
                prev_val = self.state[var_name]
                if prev_val != current_val:
                    self.dispatcher.dispatch(
                        event_type="ArrayUpdated",
                        source=var_name,
                        metadata={
                            "previous": prev_val,
                            "current": current_val
                        }
                    )
        
        # Detect deletions
        for var_name in list(self.state.keys()):
            if var_name not in current_arrays:
                self.dispatcher.dispatch(
                    event_type="ArrayDeleted",
                    source=var_name
                )
                
        self.state = current_arrays.copy()
