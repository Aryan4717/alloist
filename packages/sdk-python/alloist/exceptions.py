"""Alloist SDK exceptions."""


class AlloistPolicyDeniedError(Exception):
    """Raised when enforce() receives decision=deny from backend."""
