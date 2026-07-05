"""
AI-EVER visualizer.visualization.tree.tree_visualizer — Tree Visualizer

Detects changes to Binary Tree nodes (objects with .left and .right).
"""

from __future__ import annotations
from typing import Any, Dict
from ..base.base_visualizer import BaseVisualizer

class TreeVisualizer(BaseVisualizer):
    def __init__(self, dispatcher):
        super().__init__("TreeVisualizer", dispatcher)
        self.state: Dict[int, dict] = {} # Map id() to node state

    def process_step(self, step_data: Dict[str, Any]) -> None:
        values = step_data.get("values", {})
        
        current_nodes = {}
        
        def traverse_and_collect(val):
            if isinstance(val, dict) and "__class__" in val:
                # Is it a tree node?
                if "left" in val or "right" in val:
                    node_id = val["__id__"]
                    if node_id not in current_nodes:
                        current_nodes[node_id] = val
                        # Traverse left and right
                        left = val.get("left")
                        if left: traverse_and_collect(left)
                        right = val.get("right")
                        if right: traverse_and_collect(right)
            elif isinstance(val, list):
                for item in val:
                    traverse_and_collect(item)
            elif isinstance(val, dict):
                for k, v in val.items():
                    if k not in ("__class__", "__id__"):
                        traverse_and_collect(v)
                        
        for var_name, val in values.items():
            traverse_and_collect(val)

        # Detect creations and updates
        for node_id, current_val in current_nodes.items():
            if node_id not in self.state:
                # Created
                self.dispatcher.dispatch(
                    event_type="TreeNodeCreated",
                    source=node_id,
                    metadata={"value": current_val}
                )
            else:
                prev_val = self.state[node_id]
                
                # Check pointers
                for ptr in ["left", "right"]:
                    prev_ptr = prev_val.get(ptr, {})
                    curr_ptr = current_val.get(ptr, {})
                    
                    prev_ptr_id = prev_ptr.get("__id__") if isinstance(prev_ptr, dict) else prev_ptr
                    curr_ptr_id = curr_ptr.get("__id__") if isinstance(curr_ptr, dict) else curr_ptr
                    
                    if prev_ptr_id != curr_ptr_id:
                        self.dispatcher.dispatch(
                            event_type="TreePointerMoved",
                            source=node_id,
                            metadata={
                                "pointer": ptr,
                                "previous": prev_ptr_id,
                                "current": curr_ptr_id
                            }
                        )
                
                # Check value
                val_keys = ["val", "value", "data"]
                for k in val_keys:
                    if k in prev_val and k in current_val:
                        if prev_val[k] != current_val[k]:
                            self.dispatcher.dispatch(
                                event_type="TreeNodeUpdated",
                                source=node_id,
                                metadata={
                                    "field": k,
                                    "previous": prev_val[k],
                                    "current": current_val[k]
                                }
                            )
        
        self.state = current_nodes.copy()
