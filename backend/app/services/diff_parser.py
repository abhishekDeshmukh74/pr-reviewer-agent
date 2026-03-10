"""Diff parsing utilities."""

from __future__ import annotations

import re


def parse_diff(raw_diff: str) -> list[dict]:
    """Parse a unified diff into a list of file changes.

    Returns a list of dicts with keys: filename, language, additions, deletions, patch.
    """
    files: list[dict] = []
    current_file: dict | None = None

    ext_to_lang = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescriptreact", ".jsx": "javascriptreact",
        ".go": "go", ".rs": "rust", ".java": "java", ".rb": "ruby",
        ".cs": "csharp", ".cpp": "cpp", ".c": "c", ".swift": "swift",
        ".kt": "kotlin", ".sql": "sql", ".sh": "shell",
        ".css": "css", ".html": "html", ".md": "markdown",
        ".json": "json", ".yml": "yaml", ".yaml": "yaml",
    }

    for line in raw_diff.splitlines():
        # New file header
        diff_match = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
        if diff_match:
            if current_file:
                files.append(current_file)
            filename = diff_match.group(2)
            ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
            current_file = {
                "filename": filename,
                "language": ext_to_lang.get(ext, ""),
                "additions": [],
                "deletions": [],
                "patch_lines": [],
            }
            continue

        if current_file is None:
            continue

        current_file["patch_lines"].append(line)

        if line.startswith("+") and not line.startswith("+++"):
            current_file["additions"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current_file["deletions"].append(line[1:])

    if current_file:
        files.append(current_file)

    # Convert patch_lines to patch string
    for f in files:
        f["patch"] = "\n".join(f.pop("patch_lines"))

    return files
