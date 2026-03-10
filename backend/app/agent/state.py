"""Agent state definition for the LangGraph PR review pipeline."""

from __future__ import annotations

import operator
from typing import Annotated

from typing_extensions import TypedDict

from app.models.schemas import CategoryReview


class AgentState(TypedDict):
    """State that flows through the LangGraph agent graph."""

    # Input
    raw_diff: str
    parsed_files: list[dict]  # list of file-change dicts

    # Intermediate review results (appended by each reviewer node)
    reviews: Annotated[list[CategoryReview], operator.add]

    # Final outputs
    suggested_patch: str
    overall_summary: str
    test_suggestions: str

    # Streaming status messages
    status: str
