# Booking Agent

## What the agent does

The booking agent simulates an AI agent that creates reservations or bookings. Before creating a booking, it calls `enforce()` with the action `booking.create` and metadata (e.g. price). If Alloist allows the action, the booking is created. If not, the agent never runs the booking logic.

## How Alloist blocks dangerous actions

`enforce()` runs before the actual booking. It sends a POST request to `/enforce` with the action and metadata. If Alloist policy denies the request (e.g. price exceeds a limit), the backend returns deny and the SDK raises `AlloistPolicyDeniedError`. The agent catches this and never executes the booking. You can add policies like "deny booking.create when price > 1000" to block dangerous actions.

## Prerequisites

- Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
- Capability token minted (`python examples/create_token.py`)
- Policies applied (`python examples/apply_policies.py`) — add a policy for `booking.create` if needed
- Alloist SDK: `pip install -e packages/sdk-python`

## Run

```bash
# From repo root
ALLOIST_TOKEN=your_token python examples/booking_agent/agent.py user 50.0
```

Or with args: `python examples/booking_agent/agent.py <user> <price>`
