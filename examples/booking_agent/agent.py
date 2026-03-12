"""Booking agent - creates bookings. Alloist enforces policy before action."""
import os

from alloist import AlloistPolicyDeniedError, enforce, init

init(api_key=os.environ.get("ALLOIST_TOKEN", ""))


def create_booking(user: str, price: float) -> None:
    enforce(action="booking.create", metadata={"price": price})
    print(f"Booking created for {user} at ${price}")


if __name__ == "__main__":
    import sys

    try:
        create_booking(
            sys.argv[1] if len(sys.argv) > 1 else "user",
            float(sys.argv[2]) if len(sys.argv) > 2 else 50.0,
        )
    except AlloistPolicyDeniedError as e:
        print(f"Blocked: {e}")
