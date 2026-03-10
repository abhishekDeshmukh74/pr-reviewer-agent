"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    """Incoming review request from the frontend."""

    diff: str = Field(default="", description="Raw git diff text")
    pr_url: str = Field(default="", description="GitHub PR URL to fetch diff from")


class FileChange(BaseModel):
    """A single file changed in the diff."""

    filename: str
    language: str = ""
    additions: list[str] = Field(default_factory=list)
    deletions: list[str] = Field(default_factory=list)
    patch: str = ""


class ReviewIssue(BaseModel):
    """A single review finding."""

    file: str = ""
    line: int | None = None
    severity: str = "info"  # critical, warning, info
    title: str = ""
    description: str = ""
    suggestion: str = ""


class CategoryReview(BaseModel):
    """Review findings for one category."""

    category: str
    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str = ""


class ReviewResult(BaseModel):
    """Complete review output."""

    categories: list[CategoryReview] = Field(default_factory=list)
    suggested_patch: str = ""
    overall_summary: str = ""
    test_suggestions: str = ""
