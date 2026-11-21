import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from cost import estimate_cost


def test_zero_tokens_cost_nothing():
    assert estimate_cost(0, 0) == 0


def test_a_million_input_tokens():
    assert round(estimate_cost(1_000_000, 0), 4) == 1.0


def test_a_million_output_tokens():
    assert round(estimate_cost(0, 1_000_000), 4) == 5.0
