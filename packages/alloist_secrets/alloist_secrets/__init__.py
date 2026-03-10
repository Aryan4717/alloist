"""Secure secret management with env, AWS Secrets Manager, Vault support."""

from alloist_secrets.loader import get, get_required
from alloist_secrets.redaction import register_secret_key


class MissingSecretError(Exception):
    """Raised when a required secret is not found."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Required secret not found: {key}")


def validate_required(keys: list[str], allow_empty: bool = False) -> None:
    """
    Validate that required secrets exist at startup.
    Raises MissingSecretError if any key is missing or empty.
    allow_empty: if True, empty string is acceptable (for optional-in-dev secrets).
    """
    for key in keys:
        val = get(key)
        if val is None:
            raise MissingSecretError(key)
        if not allow_empty and val.strip() == "":
            raise MissingSecretError(key)


def start_rotation() -> None:
    """Start background secret rotation if SECRET_REFRESH_INTERVAL_SEC is set."""
    from alloist_secrets.rotation import start_rotation as _start

    _start()


__all__ = [
    "get",
    "get_required",
    "validate_required",
    "register_secret_key",
    "MissingSecretError",
    "start_rotation",
]
