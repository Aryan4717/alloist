"""Tests for policy module."""

import pytest

from cognara_enforce.policy import check_policy


def test_allows_when_scope_present() -> None:
    assert check_policy("send_email", ["email:send"])["allowed"] is True


def test_blocks_when_scope_missing() -> None:
    result = check_policy("send_email", ["read"])
    assert result["allowed"] is False
    assert "email:send" in result["reason"]


def test_allows_unknown_action() -> None:
    assert check_policy("unknown_action", [])["allowed"] is True


def test_allows_when_action_name_empty() -> None:
    assert check_policy(None, [])["allowed"] is True
