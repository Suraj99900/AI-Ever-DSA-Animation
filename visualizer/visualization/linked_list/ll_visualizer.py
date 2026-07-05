"""
AI-EVER visualizer.visualization.linked_list.ll_visualizer — Linked List Visualizer

Detects changes to Linked List nodes (objects with .next and .val).
"""

from __future__ import annotations
from typing import Any, Dict
from ..base.base_visualizer import BaseVisualizer

class LinkedListVisualizer(BaseVisualizer):
    def __init__(self, dispatcher):
        super().__init__("LLVisualizer", dispatcher)
        self.state: Dict[int, dict] = {} # Map id() to node state

    def process_step(self, step_data: Dict[str, Any]) -> None:
        values = step_data.get("values", {})
        
        current_nodes = {}
        
        def traverse_and_collect(val):
            if isinstance(val, dict) and "__class__" in val:
                # Is it a node?
                if "val" in val or "value" in val or "next" in val:
                    node_id = val["__id__"]
                    if node_id not in current_nodes:
                        current_nodes[node_id] = val
                        # Traverse next
                        nxt = val.get("next")
                        if nxt:
                            traverse_and_collect(nxt)
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
                    event_type="NodeCreated",
                    source=node_id,
                    metadata={"value": current_val}
                )
            else:
                # Compare to detect pointer rewiring or value change
                prev_val = self.state[node_id]
                # Check next pointer
                prev_next = prev_val.get("next", {})
                curr_next = current_val.get("next", {})
                
                prev_next_id = prev_next.get("__id__") if isinstance(prev_next, dict) else prev_next
                curr_next_id = curr_next.get("__id__") if isinstance(curr_next, dict) else curr_next
                
                if prev_next_id != curr_next_id:
                    self.dispatcher.dispatch(
                        event_type="PointerMoved",
                        source=node_id,
                        metadata={
                            "pointer": "next",
                            "previous": prev_next_id,
                            "current": curr_next_id
                        }
                    )
                
                # Check value
                val_keys = ["val", "value", "data"]
                for k in val_keys:
                    if k in prev_val and k in current_val:
                        if prev_val[k] != current_val[k]:
                            self.dispatcher.dispatch(
                                event_type="NodeUpdated",
                                source=node_id,
                                metadata={
                                    "field": k,
                                    "previous": prev_val[k],
                                    "current": current_val[k]
                                }
                            )

        # We don't dispatch deletions immediately for LL because they get garbage collected
        # or fall out of scope. We could detect unreachable nodes.
        
        self.state = current_nodes.copy()
