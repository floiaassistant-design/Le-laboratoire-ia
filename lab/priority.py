"""EXP-006A: deterministic, fault-blind prioritization of *existing* test inputs.

This module has no imports from buggy programs, corrected oracles or fixtures.
It consumes only arguments and builds simple structural features. No LLM/API.
"""
from __future__ import annotations

import json
from math import log2
from typing import Any


def _bucket(n: int) -> str:
    if n == 0:
        return "0"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    if n <= 4:
        return "3-4"
    if n <= 8:
        return "5-8"
    return "9+"


def features(args: tuple | list) -> frozenset[str]:
    """Bounded shape/type/value-class features; no expected outputs or bugs."""
    found: set[str] = {f"arity:{_bucket(len(args))}"}

    def visit(value: Any, pos: str, depth: int) -> None:
        if depth > 4:
            found.add(f"{pos}:deep")
            return
        if value is None:
            found.add(f"{pos}:none")
        elif isinstance(value, bool):
            found.add(f"{pos}:bool:{value}")
        elif isinstance(value, int):
            found.add(f"{pos}:int")
            found.add(f"{pos}:sign:{'negative' if value < 0 else 'zero' if value == 0 else 'positive'}")
            found.add(f"{pos}:magnitude:{_bucket(abs(value))}")
            if value != 0:
                found.add(f"{pos}:parity:{abs(value) % 2}")
                if abs(value) & (abs(value) - 1) == 0:
                    found.add(f"{pos}:power-of-two")
        elif isinstance(value, float):
            found.add(f"{pos}:float")
            found.add(f"{pos}:float-sign:{'negative' if value < 0 else 'nonnegative'}")
        elif isinstance(value, str):
            found.add(f"{pos}:str")
            found.add(f"{pos}:length:{_bucket(len(value))}")
            if value:
                found.add(f"{pos}:distinct:{_bucket(len(set(value)))}")
            if "(" in value:
                found.add(f"{pos}:left-paren")
            if ")" in value:
                found.add(f"{pos}:right-paren")
        elif isinstance(value, (list, tuple)):
            found.add(f"{pos}:sequence")
            found.add(f"{pos}:length:{_bucket(len(value))}")
            if value and all(isinstance(x, int) and not isinstance(x, bool) for x in value):
                found.add(f"{pos}:distinct:{_bucket(len(set(value)))}")
                found.add(f"{pos}:nondecreasing:{value == sorted(value)}")
                found.add(f"{pos}:contains-zero:{0 in value}")
            if value:
                # Preserve bounded structure, not every literal element.
                for index in (0, len(value) - 1):
                    visit(value[index], f"{pos}:end:{'first' if index == 0 else 'last'}", depth + 1)
                found.add(f"{pos}:nested:{any(isinstance(x, (list, tuple)) for x in value)}")
        else:
            raise TypeError(f"Unsupported test-input type: {type(value).__name__}")

    for index, arg in enumerate(args):
        visit(arg, f"arg{index}", 0)
    return frozenset(found)


def distance(left: frozenset[str], right: frozenset[str]) -> float:
    """Jaccard distance, in [0,1]."""
    union = left | right
    return len(left ^ right) / len(union) if union else 0.0


def prioritize(cases: tuple | list) -> list[int]:
    """Farthest-first traversal of test inputs, with stable input-only ties.

    First choose the structurally most atypical case (largest *mean*
    distance to other cases). Then greedily maximize the distance to the
    closest already selected case. Ties prefer mean distance to the selected
    cases, then canonical JSON representation. This is a *heuristic*.
    """
    if not cases:
        raise ValueError("Expected a non-empty sequence of tests")
    if len(cases) > 512:
        raise ValueError("Too many tests for this quadratic heuristic")
    serialized = [json.dumps(x, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":")) for x in cases]
    vectors = [features(x) for x in cases]
    n = len(vectors)
    matrix = [[distance(vectors[i], vectors[j]) for j in range(n)]
              for i in range(n)]
    order: list[int] = []
    remaining = set(range(n))
    while remaining:
        def rank(i: int):
            if not order:
                quality = sum(matrix[i]) / n
                return (-quality, 0.0, serialized[i], i)
            distances = [matrix[i][j] for j in order]
            # Smaller tuple = better: maximize nearest-neighbour distance.
            return (-min(distances), -sum(distances) / len(distances),
                    serialized[i], i)
        selected = min(remaining, key=rank)
        remaining.remove(selected)
        order.append(selected)
    return order


def prioritization_cost(n: int) -> int:
    """Upper bound on number of pairwise distance evaluations."""
    if n < 0:
        raise ValueError("Invalid number of inputs")
    return n * n
