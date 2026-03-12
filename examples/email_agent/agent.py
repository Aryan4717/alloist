"""Email agent - sends emails. Alloist enforces policy before action."""
import os

from alloist import AlloistPolicyDeniedError, enforce, init

init(api_key=os.environ.get("ALLOIST_TOKEN", ""))


def send_email(to: str) -> None:
    enforce(action="gmail.send", metadata={"to": to})
    print(f"Email sent to {to}")


if __name__ == "__main__":
    import sys

    try:
        send_email(sys.argv[1] if len(sys.argv) > 1 else "user@example.com")
    except AlloistPolicyDeniedError as e:
        print(f"Blocked: {e}")
