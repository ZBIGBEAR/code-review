#!/usr/bin/env python3
"""Code Review CLI - Multi-agent code review system."""
import sys
import click
from pathlib import Path

from .llm import review_code
from .git_utils import get_diff, get_commit_info, detect_language
from .verifier import Verifier, Scorer
from .output import format_report, format_json


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Code Review - Multi-agent code review system."""
    pass


@cli.command()
@click.argument("pr_url", required=False)
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def pr(pr_url, format):
    """Review a GitHub pull request.

    Example: code-review pr https://github.com/user/repo/pull/123
    """
    if not pr_url:
        click.echo("错误：需要提供 PR URL", err=True)
        click.echo("示例：code-review pr https://github.com/user/repo/pull/123")
        sys.exit(1)

    click.echo("🔍 正在获取 PR 代码变更...")

    # For now, we'll try to get diff from local git if available
    # Full GitHub API integration can be added later
    diff_content = _get_pr_diff(pr_url)

    if not diff_content:
        click.echo("❌ 无法获取代码变更，请确认：", err=True)
        click.echo("  1. 本地是否有对应的 git 仓库", err=True)
        click.echo("  2. 是否配置了 GitHub token", err=True)
        sys.exit(1)

    _run_review(diff_content, format)


@cli.command()
@click.option("--commit", "-c", default="HEAD~1", help="Commit to review (default: HEAD~1)")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def commit(commit, format):
    """Review a specific commit.

    Example: code-review commit --commit abc123
    """
    click.echo(f"🔍 正在审查 commit {commit}...")

    diff_content = get_diff(f"{commit}~1..{commit}")
    commit_info = get_commit_info(commit)

    if not diff_content:
        click.echo("❌ 未获取到代码变更")
        sys.exit(1)

    _run_review(diff_content, format, commit_info)


@cli.command()
@click.option("--base-branch", "-b", default="main", help="Base branch to compare (default: main)")
@click.option("--format", "-f", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def diff(base_branch, format):
    """Review uncommitted or recent changes.

    Example: code-review diff --base-branch main
    """
    click.echo(f"🔍 正在审查与 {base_branch} 的差异...")

    diff_content = get_diff(base_branch=base_branch)
    language = detect_language()

    if not diff_content:
        click.echo("❌ 未获取到代码变更")
        sys.exit(1)

    _run_review(diff_content, format, language=language)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def file(file_path, format):
    """Review a specific file.

    Example: code-review file path/to/file.py
    """
    click.echo(f"🔍 正在审查文件 {file_path}...")

    path = Path(file_path)
    if not path.exists():
        click.echo(f"❌ 文件不存在：{file_path}")
        sys.exit(1)

    diff_content = path.read_text()
    language = _detect_file_language(file_path)

    _run_review(diff_content, format, language=language)


@cli.command()
def hook():
    """Install git pre-commit hook.

    This command prints the hook script. Redirect to .git/hooks/pre-commit to install.
    """
    hook_script = """#!/bin/bash
# Code Review Pre-Commit Hook
# Installed by code-review tool

echo "🔍 Running code review..."

# Get the diff of staged files
diff_content=$(git diff --cached --staged)

if [ -z "$diff_content" ]; then
    echo "No staged changes to review."
    exit 0
fi

# Run code review
result=$(code-review --stdin 2>&1)

echo "$result"

# Check for critical issues
if echo "$result" | grep -q "Critical.*[1-9]"; then
    echo ""
    echo "❌ Review found critical issues. Please fix them before committing."
    exit 1
fi

exit 0
"""
    click.echo(hook_script)


def _run_review(diff_content, format="text", commit_info=None, language=None):
    """Run the review process."""
    if language is None:
        language = detect_language()

    click.echo(f"📝 检测到语言：{language}")
    click.echo("🤖 正在进行代码审查...")

    try:
        # Call LLM for review
        raw_output = review_code(diff_content, language)

        # Verify and parse results
        verifier = Verifier()
        issues = verifier.verify(raw_output)

        # Score results
        scorer = Scorer()
        score_info = scorer.score(issues)

        # Output results
        if format == "json":
            click.echo(format_json(issues, score_info))
        else:
            report = format_report(issues, score_info, commit_info)
            click.echo(report)

    except Exception as e:
        click.echo(f"❌ 审查失败：{e}", err=True)
        sys.exit(1)


def _get_pr_diff(pr_url: str) -> str:
    """Get diff from a PR URL.

    This is a simplified version - full implementation would use GitHub API.
    """
    # Try to get diff from local repo
    return get_diff()


def _detect_file_language(file_path: str) -> str:
    """Detect language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
    }
    ext = Path(file_path).suffix
    return ext_map.get(ext, "python")


if __name__ == "__main__":
    cli()
