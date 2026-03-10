"""GitHub API integration for fetching PR diffs."""

from __future__ import annotations

import re

import httpx

from app.config import get_settings


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, pr_number from a GitHub PR URL.

    Supports:
      - https://github.com/owner/repo/pull/123
      - https://github.com/owner/repo/pull/123/files
    """
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url
    )
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


async def fetch_pr_diff(pr_url: str) -> str:
    """Fetch the diff for a GitHub PR."""
    owner, repo, pr_number = parse_pr_url(pr_url)
    settings = get_settings()
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(api_url, headers=headers)
        resp.raise_for_status()
        return resp.text
