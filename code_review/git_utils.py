"""Git utilities for code review."""
import subprocess
from pathlib import Path
from typing import Optional


def get_diff(commit_range: Optional[str] = None, base_branch: Optional[str] = None) -> str:
    """Get git diff content.

    Args:
        commit_range: e.g. "HEAD~1" or "abc123..def456"
        base_branch: e.g. "main" or "master" (if commit_range not provided)

    Returns:
        Git diff as string
    """
    try:
        if commit_range:
            result = subprocess.run(
                ["git", "diff", commit_range],
                capture_output=True,
                text=True,
                check=False,
            )
        elif base_branch:
            result = subprocess.run(
                ["git", "diff", f"{base_branch}...HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            # Uncommitted changes
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                check=False,
            )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting diff: {e}"


def get_commit_info(ref: str = "HEAD") -> dict:
    """Get commit information."""
    try:
        # Get commit message
        msg_result = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%an%n%ae%n%s%n%b", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = msg_result.stdout.strip().split("\n")
        if len(lines) >= 4:
            return {
                "sha": lines[0],
                "author_name": lines[1],
                "author_email": lines[2],
                "subject": lines[3],
                "body": "\n".join(lines[4:]) if len(lines) > 4 else "",
            }
        return {}
    except Exception:
        return {}


def get_changed_files(commit_range: Optional[str] = None) -> list:
    """Get list of changed files."""
    try:
        if commit_range:
            result = subprocess.run(
                ["git", "diff", "--name-only", commit_range],
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
        return [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except Exception:
        return []


def detect_language() -> str:
    """Detect primary language from repo."""
    # Check common file extensions
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    files = result.stdout.split("\n")

    ext_counts = {}
    for f in files:
        if "." in f:
            ext = f.rsplit(".", 1)[-1]
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    lang_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "go": "go",
        "rs": "rust",
        "java": "java",
        "rb": "ruby",
        "php": "php",
    }

    for ext, lang in lang_map.items():
        if ext in ext_counts:
            return lang
    return "python"
