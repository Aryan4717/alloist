"""Domain utilities for email-based organization assignment."""

PERSONAL_DOMAINS = frozenset({
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
    "mail.com",
    "live.com",
    "msn.com",
    "yahoo.co.in",
    "aol.com",
    "zoho.com",
    "yandex.com",
    "gmx.com",
})


def get_email_domain(email: str) -> str:
    """Extract domain from email (lowercase). Returns empty string if invalid."""
    if not email or "@" not in email:
        return ""
    return email.split("@")[-1].lower()


def is_personal_domain(email: str) -> bool:
    """True if email domain is a known personal email provider."""
    return get_email_domain(email) in PERSONAL_DOMAINS
