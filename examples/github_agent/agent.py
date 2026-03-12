"""GitHub agent - pushes code. Alloist enforces policy before action."""
import os

from alloist import AlloistPolicyDeniedError, enforce, init

init(api_key=os.environ.get("ALLOIST_TOKEN", ""))


def push_code(branch: str = "main") -> None:
    enforce(action="github.push", metadata={"branch": branch})
    print(f"Code pushed to {branch}")


if __name__ == "__main__":
    import sys

    try:
        push_code(sys.argv[1] if len(sys.argv) > 1 else "main")
    except AlloistPolicyDeniedError as e:
        print(f"Blocked: {e}")
