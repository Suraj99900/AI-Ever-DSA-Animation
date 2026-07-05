"""
AI-EVER visualizer.algorithms.learning — Educational Explanations Engine.

Generates step-by-step pseudo-code and dynamic AI-like explanations based on AST and execution trace.
"""

from __future__ import annotations
import ast
from typing import Any

class ExplanationGenerator(ast.NodeVisitor):
    def __init__(self, code: str):
        self.code_lines = code.split("\n")
        self.explanations = {}

    def visit_Compare(self, node: ast.Compare):
        self.explanations[node.lineno] = "Comparing two elements to determine order or equality."
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.targets[0], ast.Tuple):
            self.explanations[node.lineno] = "Swapping two elements."
        else:
            self.explanations[node.lineno] = f"Assigning a value to a variable."
        self.generic_visit(node)
        
    def visit_Return(self, node: ast.Return):
        self.explanations[node.lineno] = "Returning the result from the function."
        self.generic_visit(node)
        
    def visit_For(self, node: ast.For):
        self.explanations[node.lineno] = "Iterating over elements in a sequence."
        self.generic_visit(node)
        
    def visit_While(self, node: ast.While):
        self.explanations[node.lineno] = "Looping while a condition remains true."
        self.generic_visit(node)


def generate_explanations(code: str, steps: list[dict[str, Any]]) -> None:
    """Modifies the steps list in place to add dynamic explanations."""
    generator = ExplanationGenerator(code)
    try:
        tree = ast.parse(code)
        generator.visit(tree)
    except Exception:
        pass
        
    for step in steps:
        line = step.get("line")
        base_exp = generator.explanations.get(line, "Executing this operation.")
        
        # Add dynamic runtime context
        if step.get("event") == "call":
            base_exp = f"Calling function '{step.get('func', 'unknown')}'. Establishing new stack frame."
        elif step.get("event") == "return":
            base_exp = f"Returning from function '{step.get('func', 'unknown')}'. Tearing down stack frame."
            
        step["explain"] = base_exp


def generate_pseudocode(code: str) -> list[str]:
    """Generates a pseudocode mapping of the python code."""
    pseudo = []
    for line in code.split("\n"):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        spaces = " " * indent
        
        if stripped.startswith("def "):
            pseudo.append(f"{spaces}FUNCTION {stripped[4:]}")
        elif stripped.startswith("for "):
            pseudo.append(f"{spaces}LOOP {stripped[4:]}")
        elif stripped.startswith("while "):
            pseudo.append(f"{spaces}WHILE {stripped[6:]}")
        elif stripped.startswith("if "):
            pseudo.append(f"{spaces}IF {stripped[3:]}")
        elif stripped.startswith("return "):
            pseudo.append(f"{spaces}RETURN {stripped[7:]}")
        elif stripped == "":
            pseudo.append("")
        else:
            pseudo.append(f"{spaces}EXECUTE {stripped}")
            
    return pseudo
