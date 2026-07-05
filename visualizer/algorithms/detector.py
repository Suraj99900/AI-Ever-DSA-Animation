"""
AI-EVER visualizer.algorithms.detector — Algorithm Detection Engine.

Analyzes Python source code to detect common algorithms using AST heuristics.
"""

from __future__ import annotations
import ast

class AlgorithmDetector(ast.NodeVisitor):
    def __init__(self):
        self.algorithms = {
            "Bubble Sort": 0,
            "Selection Sort": 0,
            "Insertion Sort": 0,
            "Binary Search": 0,
            "Linear Search": 0,
        }
        self.loop_depth = 0
        self.in_if = False

    def detect(self, code: str) -> dict[str, str | float]:
        try:
            tree = ast.parse(code)
            self.visit(tree)
            
            # Very basic heuristics for Phase 5 MVP
            if self.algorithms["Bubble Sort"] > 0:
                return {"algorithm": "Bubble Sort", "confidence": 0.85}
            elif self.algorithms["Binary Search"] > 0:
                return {"algorithm": "Binary Search", "confidence": 0.90}
            elif self.algorithms["Linear Search"] > 0:
                return {"algorithm": "Linear Search", "confidence": 0.70}
                
            return {"algorithm": "Unknown", "confidence": 0.0}
        except Exception:
            return {"algorithm": "Unknown", "confidence": 0.0}

    def visit_For(self, node: ast.For):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_If(self, node: ast.If):
        old_in_if = self.in_if
        self.in_if = True
        
        # Check for linear search (if x == target: return)
        if self.loop_depth == 1:
            for child in node.body:
                if isinstance(child, ast.Return):
                    self.algorithms["Linear Search"] += 1
        
        self.generic_visit(node)
        self.in_if = old_in_if

    def visit_Assign(self, node: ast.Assign):
        # Check for swap: a, b = b, a
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            if self.loop_depth >= 2 and self.in_if:
                self.algorithms["Bubble Sort"] += 1

        # Check for Binary search mid calculation
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id in ["mid", "middle"]:
                    self.algorithms["Binary Search"] += 1
                
        self.generic_visit(node)
        
    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.FloorDiv):
            self.algorithms["Binary Search"] += 1
        self.generic_visit(node)


def detect_algorithm(code: str) -> dict[str, str | float]:
    detector = AlgorithmDetector()
    return detector.detect(code)
