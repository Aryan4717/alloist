"""Compile policy DSL expressions into evaluator rules."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.policy_dsl import DslRule


def _parse_literal(s: str) -> Any:
    """Parse a string literal to Python value."""
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1].replace('\\"', '"')
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("\\'", "'")
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() == "null":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def parse_condition(expr: str) -> dict[str, Any] | None:
    """
    Parse a single condition expression into {field, operator, value}.
    Returns None if expression is action.service or action.name (handled separately).
    Raises ValueError on parse error.
    """
    expr = expr.strip()
    if not expr:
        return None

    # action.service == "stripe" -> special case, return None (handled in compile_rule)
    if expr.startswith("action.service"):
        return None
    if expr.startswith("action.name"):
        return None

    # "email:send" in token.scopes  (supports " or ' quoted literals)
    in_match = re.match(r'^(["\'])(.+?)\1\s+in\s+(\S+(?:\.\S+)*)\s*$', expr)
    if in_match:
        literal = in_match.group(2)  # unescaped content
        field = in_match.group(3).strip()
        return {"field": field, "operator": "contains", "value": literal}

    # metadata.amount > 1000, metadata.currency == "usd", etc.
    ops = [
        ("==", "eq"),
        ("!=", "ne"),
        (">=", "gte"),
        ("<=", "lte"),
        (">", "gt"),
        ("<", "lt"),
    ]
    for op_str, op_name in ops:
        if op_str in expr:
            parts = expr.split(op_str, 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid expression: {expr}")
            lhs = parts[0].strip()
            rhs = parts[1].strip()
            if not lhs or not rhs:
                raise ValueError(f"Invalid expression: {expr}")
            value = _parse_literal(rhs)
            return {"field": lhs, "operator": op_name, "value": value}

    raise ValueError(f"Unsupported expression: {expr}")


def _parse_action_match(expr: str) -> tuple[str, str] | None:
    """Parse action.service == 'x' or action.name == 'y'. Returns (key, value) or None."""
    expr = expr.strip()
    if expr.startswith("action.service") and "==" in expr:
        parts = expr.split("==", 1)
        if len(parts) == 2:
            value = _parse_literal(parts[1].strip())
            return ("service", str(value))
    if expr.startswith("action.name") and "==" in expr:
        parts = expr.split("==", 1)
        if len(parts) == 2:
            value = _parse_literal(parts[1].strip())
            return ("action_name", str(value))
    return None


def compile_rule(dsl_rule: DslRule) -> dict[str, Any]:
    """
    Compile a single DSL rule into evaluator rules dict.
    """
    match: dict[str, str] = {"service": "*", "action_name": "*"}
    conditions: list[dict[str, Any]] = []
    errors: list[str] = []

    for i, expr in enumerate(dsl_rule.conditions):
        expr = expr.strip()
        if not expr:
            continue
        try:
            action_match = _parse_action_match(expr)
            if action_match:
                key, value = action_match
                match[key] = value
                continue
            cond = parse_condition(expr)
            if cond:
                conditions.append(cond)
        except ValueError as e:
            errors.append(f"Condition {i + 1}: {e}")

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "effect": dsl_rule.effect,
        "match": match,
        "conditions": conditions,
    }


def compile_document(rules: list[DslRule]) -> tuple[dict[str, Any], list[str]]:
    """
    Compile a list of DSL rules. For v1 we take the first rule only (single rule per policy).
    Returns (compiled_rules, errors).
    """
    if not rules:
        return {}, ["At least one rule required"]
    errors: list[str] = []
    try:
        compiled = compile_rule(rules[0])
        return compiled, []
    except ValueError as e:
        return {}, [str(e)]
