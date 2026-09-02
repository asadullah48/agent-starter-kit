"""Tests for the calculator and knowledge-base tools."""

import pytest

from tools.calculator import calculator
from tools import execute_tool


def test_calculator_basic_ops():
    assert calculator("2 + 3") == "5"
    assert calculator("(3 + 4) * 2") == "14"
    assert calculator("2 ** 10") == "1024"


def test_calculator_rejects_unsafe_input():
    with pytest.raises(Exception):
        calculator("__import__(''os'').system(''echo hi'')")


def test_execute_tool_unknown_name_is_an_error_not_a_crash():
    result, is_error = execute_tool("does_not_exist", {})
    assert is_error is True
    assert "Unknown tool" in result


def test_execute_tool_bad_args_is_an_error_not_a_crash():
    result, is_error = execute_tool("calculator", {"expression": "not math"})
    assert is_error is True
