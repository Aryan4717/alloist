"""Schemas for policy DSL compile API."""

from typing import Any

from pydantic import BaseModel, Field


class DslRule(BaseModel):
    """Single rule in the policy DSL."""

    id: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    conditions: list[str] = Field(default_factory=list)
    effect: str = Field(..., pattern="^(allow|deny)$")


class CompileDslRequest(BaseModel):
    """Request body for compile_dsl endpoint."""

    rules: list[DslRule] = Field(..., min_length=1)


class CompileDslResponse(BaseModel):
    """Response from compile_dsl endpoint."""

    rules: dict[str, Any] | None = None
    errors: list[str] | None = None
