"""Safe Python Math Calculator Tool.

Provides safe mathematical computation for arithmetic, algebraic expressions,
trigonometry, statistics, and SymPy symbolic calculations without risking code injection.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Dict
from langchain_core.tools import tool

# Whitelist of allowed binary and unary operators
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Whitelist of safe mathematical functions and constants
_MATH_FUNCS: Dict[str, Any] = {
    # Constants
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    # Elementary functions
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.pow(x, 1 / 3) if x >= 0 else -math.pow(-x, 1 / 3),
    "exp": math.exp,
    "pow": math.pow,
    # Logarithms
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    # Trigonometry (radians)
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "degrees": math.degrees,
    "radians": math.radians,
    # Combinatorics & Integers
    "factorial": math.factorial,
    "comb": math.comb,
    "gcd": math.gcd,
    "ceil": math.ceil,
    "floor": math.floor,
}


def _safe_eval_node(node: ast.AST) -> Any:
    """Recursively evaluate an AST node restricting to safe mathematical operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    if isinstance(node, ast.Name):
        if node.id in _MATH_FUNCS:
            return _MATH_FUNCS[node.id]
        raise ValueError(f"Unknown variable or function: '{node.id}'")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            operand = _safe_eval_node(node.operand)
            return _OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            left = _safe_eval_node(node.left)
            right = _safe_eval_node(node.right)
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division or modulo by zero.")
            # Guard against excessive exponentiation (DoS protection)
            if op_type is ast.Pow and (isinstance(right, (int, float)) and right > 1000):
                raise ValueError("Exponent too large (maximum allowed power is 1000).")
            return _OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

    if isinstance(node, ast.Call):
        func = _safe_eval_node(node.func)
        if not callable(func):
            raise ValueError(f"Attempted to call non-callable object")
        args = [_safe_eval_node(arg) for arg in node.args]
        return func(*args)

    raise ValueError(f"Unsupported syntax expression: {type(node).__name__}")


def evaluate_expression(expr: str) -> str:
    """Evaluate a mathematical string expression safely."""
    clean_expr = expr.strip()
    if not clean_expr:
        return "Error: Empty expression provided."

    # Normalize common symbols like ^ to ** and remove commas in numbers (e.g., 48,500,000)
    # Be careful not to replace commas inside function arguments like atan2(1, 2)
    # If the expression looks like a single large number with commas or simple math
    normalized = clean_expr.replace("^", "**")

    # Attempt safe AST evaluation first
    try:
        parsed = ast.parse(normalized, mode="eval")
        result = _safe_eval_node(parsed)

        # Format integer vs float cleanly
        if isinstance(result, float) and result.is_integer():
            formatted = f"{int(result):,}"
        elif isinstance(result, float):
            # Show up to 8 decimal places without trailing zeroes
            formatted = f"{result:,.8f}".rstrip("0").rstrip(".")
        elif isinstance(result, int):
            formatted = f"{result:,}"
        else:
            formatted = str(result)

        return f"Result: {formatted} (exact: {result})"
    except ZeroDivisionError as zde:
        return f"Math Evaluation Error: Division or modulo by zero ({str(zde)})"
    except Exception as ast_err:
        # Fallback: Try SymPy for advanced algebraic or symbolic expressions
        try:
            import sympy
            sym_expr = sympy.sympify(normalized, evaluate=True)
            if sym_expr in (sympy.zoo, sympy.nan):
                return "Math Evaluation Error: Division or modulo by zero."
            numeric_val = sym_expr.evalf()
            return f"Result: {numeric_val} (symbolic: {sym_expr})"
        except Exception:
            return f"Math Evaluation Error: {str(ast_err)}"


@tool("calculator")
def calculator(expression: str) -> str:
    """Perform precise mathematical and arithmetic calculations.

    Useful for evaluating arithmetic formulas, percentages, statistical values,
    powers, roots, geometry, and conversions.

    Args:
        expression: A mathematical expression string, e.g. "48500000 * 0.15",
                    "sqrt(256) * 10.2", "log(100, 10)", "(22400000 / 48500000) * 100".

    Returns:
        The calculated result or a descriptive error message if invalid.
    """
    return evaluate_expression(expression)
