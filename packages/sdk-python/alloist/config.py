"""Module-level config for Alloist SDK."""

_api_key: str | None = None
_policy_service_url: str = "http://localhost:8001"


def init(
    api_key: str,
    policy_service_url: str | None = None,
) -> None:
    """Initialize the SDK with API key (capability token) and optional policy service URL."""
    global _api_key, _policy_service_url
    _api_key = api_key
    if policy_service_url is not None:
        _policy_service_url = policy_service_url.rstrip("/")


def get_api_key() -> str | None:
    return _api_key


def get_policy_service_url() -> str:
    return _policy_service_url
