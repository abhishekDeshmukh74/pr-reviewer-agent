"""Tests for GitHub URL parser."""

import pytest

from app.services.github import parse_pr_url


def test_parse_standard_url():
    owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/12345")
    assert owner == "facebook"
    assert repo == "react"
    assert num == 12345


def test_parse_url_with_files_tab():
    owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/99/files")
    assert owner == "owner"
    assert repo == "repo"
    assert num == 99


def test_parse_invalid_url():
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_pr_url("https://github.com/owner/repo/issues/1")


def test_parse_not_github():
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_pr_url("https://gitlab.com/owner/repo/pull/1")
