# Alloist Python SDK

Simple policy enforcement for AI agents. Gate actions with one line of code.

## Install

```bash
pip install -e packages/sdk-python
```

## Usage

```python
from alloist import init, enforce

# Initialize with your capability token (from minting)
init(api_key="ALLOIST_TOKEN")

# Enforce before performing an action
enforce(action="gmail.send", metadata={"to": "user@gmail.com"})
# Returns on allow; raises AlloistPolicyDeniedError on deny

# Proceed with your action
send_email(to="user@gmail.com", body="...")
```

## Example

```python
from alloist import init, enforce, AlloistPolicyDeniedError

init(api_key="eyJ...")  # Your capability token

try:
    enforce(action="gmail.send", metadata={"to": "user@gmail.com"})
    # Action allowed - proceed
    send_email(to="user@gmail.com", body="Hello")
except AlloistPolicyDeniedError:
    # Action blocked by policy
    print("Cannot send email - policy denied")
```

## Configuration

Default policy service URL: `http://localhost:8001`

Override with:

```python
init(api_key="...", policy_service_url="https://policy.example.com")
```

## Requirements

- Python 3.10+
- Alloist policy service running with `/enforce` endpoint
