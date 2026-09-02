"""A calculator tool.

Uses Python's `ast` module to evaluate only a whitelist of arithmetic
node types -- no `eval()`/`exec()`, so the model can never use this tool
to run arbitrary code.
"""

from __future__ import annotations

import ast
import operator

TOOL_DEF = {
    "name": "calculator",
    "description": (
        "Evaluate a basic arithmetic expression (+, -, *, /, **, parentheses). "
        "Use this for any math instead of computing it yourself."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "An arithmetic expression, e.g. '(3 + 4) * 2'.",
            }
        },
        "required": ["expression"],
    },
}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> str:
    """Safely evaluate `expression` and return the result as a string."""
    tree = ast.parse(expression, mode="eval")
    result = _eval(tree.body)
    return str(result)
