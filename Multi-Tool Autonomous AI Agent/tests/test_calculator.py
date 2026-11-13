"""Unit tests for the Calculator tool."""

import pytest
from agent.tools.calculator import calculator, evaluate_expression


def test_basic_arithmetic():
    res = calculator.invoke({"expression": "25 + 75 * 2"})
    assert "Result: 175" in res


def test_percentage_calculation():
    # 20% of 48,500,000
    res = calculator.invoke({"expression": "48500000 * 0.20"})
    assert "9,700,000" in res


def test_ratio_percentage():
    # (9,700,000 / 48,500,000) * 100 = 20.0%
    res = calculator.invoke({"expression": "(9700000 / 48500000) * 100"})
    assert "20" in res


def test_math_functions():
    # Square root
    res_sqrt = calculator.invoke({"expression": "sqrt(256)"})
    assert "16" in res_sqrt

    # Absolute value & power
    res_pow = calculator.invoke({"expression": "pow(2, 8)"})
    assert "256" in res_pow

    # Trigonometry & constants
    res_pi = calculator.invoke({"expression": "round(sin(pi / 2), 4)"})
    assert "1" in res_pi


def test_zero_division():
    res = calculator.invoke({"expression": "100 / 0"})
    assert "Division or modulo by zero" in res or "Math Evaluation Error" in res


def test_empty_expression():
    res = calculator.invoke({"expression": "   "})
    assert "Error: Empty expression" in res


def test_syntax_error():
    res = calculator.invoke({"expression": "25 ++** 5"})
    assert "Math Evaluation Error" in res
