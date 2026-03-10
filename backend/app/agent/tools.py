"""Tools available to the PR review agent."""

from __future__ import annotations

import json
import re

from langchain_core.tools import tool


@tool
def count_lines(diff: str) -> dict:
    """Count added/removed lines in a diff to gauge change size."""
    added = len([l for l in diff.splitlines() if l.startswith("+")])
    removed = len([l for l in diff.splitlines() if l.startswith("-")])
    return {"added": added, "removed": removed, "total": added + removed}


@tool
def detect_languages(filenames: list[str]) -> list[str]:
    """Detect programming languages from filenames."""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".jsx": "JavaScript (React)",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".sql": "SQL",
        ".sh": "Shell",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".json": "JSON",
        ".md": "Markdown",
        ".css": "CSS",
        ".html": "HTML",
    }
    langs = set()
    for f in filenames:
        for ext, lang in ext_map.items():
            if f.endswith(ext):
                langs.add(lang)
                break
    return sorted(langs)


@tool
def extract_function_names(diff: str) -> list[str]:
    """Extract function/method names that appear in the diff."""
    patterns = [
        r"def\s+(\w+)",           # Python
        r"function\s+(\w+)",      # JS/TS
        r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(",  # JS arrow
        r"func\s+(\w+)",          # Go
        r"fn\s+(\w+)",            # Rust
    ]
    names = set()
    for pattern in patterns:
        names.update(re.findall(pattern, diff))
    return sorted(names)


@tool
def validate_json(text: str) -> dict:
    """Check if a string is valid JSON and return parsed result or error."""
    try:
        parsed = json.loads(text)
        return {"valid": True, "data": parsed}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}
