#!/usr/bin/env python3
"""CLI to create policies. Usage: python -m app.cli.create_policy --name "..." --effect deny --service stripe --action charge --condition metadata.amount:gt:1000"""

import argparse
import json
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import SessionLocal
from app.models.policy import Policy


def parse_condition(cond_str: str) -> dict:
    """Parse condition string like 'metadata.amount:gt:1000' into {field, operator, value}."""
    parts = cond_str.split(":")
    if len(parts) != 3:
        raise ValueError(f"Condition must be field:operator:value, got: {cond_str}")
    field, operator, value_str = parts
    # Try to parse value as number
    try:
        value = int(value_str)
    except ValueError:
        try:
            value = float(value_str)
        except ValueError:
            value = value_str
    return {"field": field, "operator": operator, "value": value}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a policy")
    parser.add_argument("--name", required=True, help="Policy name")
    parser.add_argument("--description", default="", help="Policy description")
    parser.add_argument("--effect", choices=["allow", "deny"], default="deny")
    parser.add_argument("--service", default="*", help="Service to match (use * for any)")
    parser.add_argument("--action", default="*", help="Action name to match (use * for any)")
    parser.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        default=[],
        metavar="FIELD:OP:VALUE",
        help="Condition e.g. metadata.amount:gt:1000 (repeat for multiple)",
    )
    args = parser.parse_args()

    conditions = []
    for c in args.conditions:
        try:
            conditions.append(parse_condition(c))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    rules = {
        "effect": args.effect,
        "match": {
            "service": args.service,
            "action_name": args.action,
        },
        "conditions": conditions,
    }

    db = SessionLocal()
    try:
        policy = Policy(
            name=args.name,
            description=args.description or None,
            rules=rules,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        print(json.dumps({"id": str(policy.id), "name": policy.name, "rules": policy.rules}, indent=2))
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
