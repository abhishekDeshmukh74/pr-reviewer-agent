"""LangGraph node functions for the PR review pipeline."""

from __future__ import annotations

import json
import logging
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.prompts import (
    CATEGORY_CONFIGS,
    CATEGORY_REVIEW_PROMPT_TEMPLATE,
    PATCH_PROMPT,
    SUMMARY_PROMPT,
)
from app.agent.state import AgentState
from app.config import get_settings
from app.models.schemas import CategoryReview, ReviewIssue
from app.services.diff_parser import parse_diff

logger = logging.getLogger(__name__)


def _invoke_with_retry(llm, messages, max_retries: int = 6):
    """Invoke the LLM, honouring Groq's rate-limit retry-after delay on 429s."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            err = str(e)
            if "rate_limit_exceeded" in err or "429" in err:
                match = re.search(r"try again in ([\d.]+)s", err)
                wait = float(match.group(1)) + 1.0 if match else 2 ** attempt * 5.0
                logger.warning(
                    "Rate limit hit — waiting %.1fs before retry %d/%d",
                    wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
            else:
                raise
    return llm.invoke(messages)


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0,
    )


def _safe_parse_json(text: str) -> dict | list | None:
    """Parse JSON from LLM output, stripping markdown fences if present."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Strip markdown code fences
        lines = cleaned.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM output: %s", cleaned[:200])
        return None


# ─── Node: parse_diff ────────────────────────────────────────────────

def parse_diff_node(state: AgentState) -> dict:
    """Parse the raw diff into structured file changes."""
    files = parse_diff(state["raw_diff"])
    return {"parsed_files": files, "status": f"Parsed {len(files)} file(s)"}


# ─── Node: guardrail_check ──────────────────────────────────────────

MAX_DIFF_LINES = 3000

def guardrail_check(state: AgentState) -> dict:
    """Validate input before running expensive LLM calls."""
    diff = state["raw_diff"]
    line_count = len(diff.splitlines())

    if line_count == 0:
        raise ValueError("Empty diff — nothing to review.")

    if line_count > MAX_DIFF_LINES:
        raise ValueError(
            f"Diff is too large ({line_count} lines). "
            f"Maximum supported is {MAX_DIFF_LINES} lines. "
            "Consider splitting into smaller PRs."
        )

    return {"status": "Guardrails passed"}


# ─── Node factory: category reviewer ────────────────────────────────

def _make_category_reviewer(category_key: str):
    """Create a node function that reviews for a specific category."""
    config = CATEGORY_CONFIGS[category_key]

    def reviewer_node(state: AgentState) -> dict:
        llm = _get_llm()
        prompt = CATEGORY_REVIEW_PROMPT_TEMPLATE.format(
            category=config["category"],
            focus_areas=config["focus_areas"],
            diff=state["raw_diff"],
        )
        response = _invoke_with_retry(llm, [
            SystemMessage(content="You are an expert code reviewer. Return only valid JSON."),
            HumanMessage(content=prompt),
        ])

        parsed = _safe_parse_json(response.content)
        if parsed is None:
            return {
                "reviews": [
                    CategoryReview(
                        category=config["category"],
                        issues=[],
                        summary=f"Failed to parse {config['category']} review output.",
                    )
                ],
                "status": f"Reviewed: {config['category']} (parse error)",
            }

        issues = []
        for item in parsed.get("issues", []):
            issues.append(ReviewIssue(**item))

        return {
            "reviews": [
                CategoryReview(
                    category=config["category"],
                    issues=issues,
                    summary=parsed.get("summary", ""),
                )
            ],
            "status": f"Reviewed: {config['category']} ({len(issues)} issue(s))",
        }

    reviewer_node.__name__ = f"review_{category_key}"
    return reviewer_node


# Create reviewer nodes for each category
review_bugs = _make_category_reviewer("bugs")
review_security = _make_category_reviewer("security")
review_performance = _make_category_reviewer("performance")
review_readability = _make_category_reviewer("readability")
review_tests = _make_category_reviewer("tests")


# ─── Node: generate_patch ───────────────────────────────────────────

def generate_patch(state: AgentState) -> dict:
    """Generate a suggested fix patch based on findings."""
    llm = _get_llm()
    findings_text = "\n\n".join(
        f"### {r.category}\n{r.summary}\n"
        + "\n".join(
            f"- [{i.severity}] {i.title}: {i.description}" for i in r.issues
        )
        for r in state["reviews"]
    )

    if not any(r.issues for r in state["reviews"]):
        return {"suggested_patch": "", "status": "No issues found — skipping patch generation"}

    prompt = PATCH_PROMPT.format(diff=state["raw_diff"], findings=findings_text)
    response = _invoke_with_retry(llm, [
        SystemMessage(content="You are a senior engineer. Return only a unified diff patch."),
        HumanMessage(content=prompt),
    ])
    patch = response.content.strip()
    # Strip markdown fences if present
    if patch.startswith("```"):
        lines = patch.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        patch = "\n".join(lines)
    return {"suggested_patch": patch, "status": "Generated suggested patch"}


# ─── Node: generate_summary ─────────────────────────────────────────

def generate_summary(state: AgentState) -> dict:
    """Generate overall summary and test suggestions."""
    llm = _get_llm()
    findings_text = "\n\n".join(
        f"### {r.category}\n{r.summary}\n"
        + "\n".join(
            f"- [{i.severity}] {i.title}: {i.description}" for i in r.issues
        )
        for r in state["reviews"]
    )

    prompt = SUMMARY_PROMPT.format(findings=findings_text)
    response = _invoke_with_retry(llm, [
        SystemMessage(content="You are a senior engineer. Return only valid JSON."),
        HumanMessage(content=prompt),
    ])

    parsed = _safe_parse_json(response.content)
    if parsed is None:
        return {
            "overall_summary": "Review complete. See category details above.",
            "test_suggestions": "",
            "status": "Summary generated (parse error)",
        }

    return {
        "overall_summary": parsed.get("overall_summary", ""),
        "test_suggestions": parsed.get("test_suggestions", ""),
        "status": "Review complete",
    }
