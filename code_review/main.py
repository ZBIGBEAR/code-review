#!/usr/bin/env python3
"""Code Review CLI - Agent loop based code review system."""
import os
import sys
import json
import click
from pathlib import Path

from .llm import chat, SYSTEM, TOOLS
from .output import format_report, format_json, format_markdown, save_report


TOOL_HANDLERS = {}


def setup_tool_handlers():
    """Setup tool handlers for executing AI tool calls."""
    import subprocess
    import os

    def run_bash(command: str) -> str:
        """Execute shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (result.stdout + result.stderr).strip()
            return output[:50000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"
        except Exception as e:
            return f"Error: {e}"

    def run_read(path: str, limit: int = None) -> str:
        """Read file content."""
        try:
            content = Path(path).read_text()
            lines = content.splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    global TOOL_HANDLERS
    TOOL_HANDLERS = {
        "bash": run_bash,
        "read_file": run_read,
    }


def execute_tool_call(block) -> dict:
    """Execute a single tool call from AI response."""
    tool_name = block.name
    tool_input = dict(block.input or {})

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Unknown tool: {tool_name}",
        }

    try:
        if tool_name == "bash":
            output = handler(tool_input.get("command", ""))
        elif tool_name == "read_file":
            output = handler(
                tool_input.get("path", ""),
                tool_input.get("limit"),
            )
        else:
            output = handler(**tool_input)
    except Exception as e:
        output = f"Error executing {tool_name}: {e}"

    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": output,
    }


def agent_loop(messages: list) -> dict:
    """Main agent loop - AI calls tools until review is done."""
    tools = TOOLS
    max_iterations = 50
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call AI
        response = chat(messages, system=SYSTEM, tools=tools)

        # Add AI response to messages
        messages.append({
            "role": "assistant",
            "content": response.content,
        })

        # Check if AI stopped without tool use
        if response.stop_reason != "tool_use":
            # AI finished without calling browse_codebase
            text_content = _extract_text(response.content)
            return {
                "error": f"AI stopped unexpectedly: {response.stop_reason}",
                "output": text_content,
            }

        # Collect tool results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool_call(block)
                tool_results.append(result)

                # Check if this is the browse_codebase call with "done"
                if block.name == "browse_codebase":
                    try:
                        result_json = json.loads(result["content"])
                        # Review completed
                        return result_json
                    except (json.JSONDecodeError, KeyError):
                        pass

        # Add tool results to messages
        messages.append({
            "role": "user",
            "content": tool_results,
        })

    return {"error": "Max iterations reached"}


def _extract_text(content) -> str:
    """Extract text content from AI response."""
    if not isinstance(content, list):
        return str(content) if content else ""
    texts = []
    for block in content:
        if hasattr(block, "text") and block.text:
            texts.append(block.text)
    return "\n".join(texts) if texts else ""


@click.group()
@click.version_option(version="0.3.0")
def cli():
    """Code Review - Agent-based code review system."""
    pass


@cli.command()
@click.argument("pr_url", required=False)
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def pr(pr_url, format):
    """Review a GitHub pull request.

    Example: code-review pr https://github.com/user/repo/pull/123
    """
    if not pr_url:
        click.echo("Error: PR URL is required", err=True)
        click.echo("Example: code-review pr https://github.com/user/repo/pull/123")
        sys.exit(1)

    setup_tool_handlers()

    click.echo("🔍 Getting PR code changes...")

    # Get diff from local git (assumes you're in the repo)
    import subprocess
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--no-color"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff_content = diff_result.stdout or diff_result.stderr
    except Exception as e:
        click.echo(f"Error getting diff: {e}", err=True)
        sys.exit(1)

    if not diff_content.strip():
        click.echo("No code changes found.")
        sys.exit(0)

    # Get changed files list
    try:
        files_result = subprocess.run(
            ["git", "diff", "--name-only", "--no-color"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        changed_files = [f.strip() for f in files_result.stdout.split("\n") if f.strip()]
    except Exception:
        changed_files = []

    # Get commit info if available
    commit_info = {}
    try:
        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%an%n%ae%n%s", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = log_result.stdout.strip().split("\n")
        if len(lines) >= 4:
            commit_info = {
                "sha": lines[0],
                "author": lines[1],
                "email": lines[2],
                "subject": lines[3],
            }
    except Exception:
        pass

    _run_review(diff_content, changed_files, format, commit_info)


@cli.command()
@click.option("--commit", "-c", default="HEAD~1", help="Commit to review (default: HEAD~1)")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def commit(commit, format):
    """Review a specific commit.

    Example: code-review commit --commit abc123
    """
    setup_tool_handlers()

    click.echo(f"🔍 Reviewing commit {commit}...")

    import subprocess
    try:
        # Get commit info
        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%an%n%ae%n%s%n%b", commit],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = log_result.stdout.strip().split("\n")
        commit_info = {
            "sha": lines[0] if len(lines) > 0 else "",
            "author": lines[1] if len(lines) > 1 else "",
            "email": lines[2] if len(lines) > 2 else "",
            "subject": lines[3] if len(lines) > 3 else "",
            "body": "\n".join(lines[4:]) if len(lines) > 4 else "",
        }

        # Get diff for this commit
        diff_result = subprocess.run(
            ["git", "diff", f"{commit}~1..{commit}", "--no-color"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff_content = diff_result.stdout

        # Get changed files
        files_result = subprocess.run(
            ["git", "diff", f"{commit}~1..{commit}", "--name-only", "--no-color"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        changed_files = [f.strip() for f in files_result.stdout.split("\n") if f.strip()]

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not diff_content.strip():
        click.echo("No code changes found.")
        sys.exit(0)

    _run_review(diff_content, changed_files, format, commit_info)


@cli.command()
@click.option("--base-branch", "-b", default="main", help="Base branch to compare (default: main)")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def diff(base_branch, format):
    """Review uncommitted or recent changes.

    Example: code-review diff --base-branch main

    Can also accept diff via stdin (used by pre-commit hook).
    """
    setup_tool_handlers()

    import subprocess
    import sys

    # Check if stdin has content (from hook)
    stdin_content = ""
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read()

    if stdin_content.strip():
        # Use stdin content from hook
        diff_content = stdin_content
        # Read changed files from environment variable
        changed_files = []
        changed_files_file = os.environ.get("CHANGED_FILES_FILE")
        if changed_files_file and Path(changed_files_file).exists():
            changed_files = [line.strip() for line in Path(changed_files_file).read_text().splitlines() if line.strip()]
        click.echo(f"📝 Using diff from stdin... ({len(changed_files)} files)")
    else:
        # Get diff from git
        click.echo(f"🔍 Reviewing changes compared to {base_branch}...")
        try:
            diff_result = subprocess.run(
                ["git", "diff", f"{base_branch}...HEAD", "--no-color"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            diff_content = diff_result.stdout

            files_result = subprocess.run(
                ["git", "diff", f"{base_branch}...HEAD", "--name-only", "--no-color"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            changed_files = [f.strip() for f in files_result.stdout.split("\n") if f.strip()]
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    if not diff_content.strip():
        click.echo("No code changes found.")
        sys.exit(0)

    _run_review(diff_content, changed_files, format)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text", help="Output format")
def file(file_path, format):
    """Review a specific file.

    Example: code-review file path/to/file.py
    """
    setup_tool_handlers()

    click.echo(f"🔍 Reviewing file {file_path}...")

    try:
        content = Path(file_path).read_text()
        diff_content = f"File: {file_path}\n\n{content}"
        changed_files = [file_path]
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)

    _run_review(diff_content, changed_files, format)


def _run_review(diff_content: str, changed_files: list, format: str = "text",
                commit_info: dict = None, output: str = None, pr_url: str = None):
    """Run the review using agent loop.

    Args:
        diff_content: Git diff content
        changed_files: List of changed files
        format: Output format (text/json)
        commit_info: Commit information
        output: Output directory for markdown report (default: reports/)
    """
    click.echo(f"📝 Changed files: {len(changed_files)}")
    click.echo("🤖 Starting agent-based code review...")

    # Build initial messages
    changed_files_str = "\n".join(f"- {f}" for f in changed_files) if changed_files else "No files"
    initial_message = f"""请审查以下代码变更。

## 变更的文件列表
{changed_files_str}

## Git Diff
{diff_content}

请开始审查：
1. 首先了解项目结构（使用 ls, find 等命令）
2. 阅读修改的文件内容，理解改动意图
3. 探索可能受影响的未修改代码
4. 完成审查后，调用 browse_codebase 工具返回结果
"""

    messages = [{"role": "user", "content": initial_message}]

    try:
        result = agent_loop(messages)

        if "error" in result and "output" not in result:
            click.echo(f"❌ {result['error']}", err=True)
            sys.exit(1)

        # Extract issues and score
        issues = result.get("issues", [])
        score_info = {
            "score": result.get("score", 0),
            "rating": result.get("rating", "?"),
            "verdict": result.get("summary", ""),
            "critical": sum(1 for i in issues if i.get("severity") == "critical"),
            "warning": sum(1 for i in issues if i.get("severity") == "warning"),
            "suggestion": sum(1 for i in issues if i.get("severity") == "suggestion"),
        }

        # Save markdown report
        if output is None:
            output = "reports"
        report_path = save_report(issues, score_info, commit_info, changed_files, pr_url, output)
        click.echo(f"📄 报告已保存: {report_path}")

        # Output results
        if format == "json":
            click.echo(format_json(issues, score_info))
        else:
            report = format_report(issues, score_info, commit_info)
            click.echo(report)

        # Exit with error if critical issues found
        if score_info["critical"] > 0:
            sys.exit(1)

    except Exception as e:
        import traceback
        click.echo(f"❌ Review failed: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def hook():
    """Print git pre-commit hook script."""
    hook_script = '''#!/bin/bash
# Code Review Pre-Commit Hook
# Usage: code-review hook > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

echo "🔍 Running code review on staged changes..."

# Get staged changes
diff_content=$(git diff --cached --diff-filter=ACMR --staged)
changed_files=$(git diff --cached --name-only --diff-filter=ACMR --staged | tr '\\n' ' ')

if [ -z "$diff_content" ]; then
    echo "No staged changes to review."
    exit 0
fi

echo "Changed files: $changed_files"
echo ""

# Save changed files to temp file for the diff command
CHANGED_FILES_TMP=$(mktemp)
echo "$changed_files" | tr ' ' '\\n' | grep -v '^$' > "$CHANGED_FILES_TMP"

# Find Python with code_review module installed
for py in "/opt/homebrew/Caskroom/miniconda/base/bin/python3" "/usr/local/bin/python3" "$HOME/miniconda3/bin/python3" "$HOME/anaconda3/bin/python3" "python3"; do
    if $py -c "import code_review" 2>/dev/null; then
        PYTHON_BIN=$py
        break
    fi
done
PYTHON_BIN=${PYTHON_BIN:-python3}

# Run code review with reports output
result=$(echo "$diff_content" | CHANGED_FILES_FILE="$CHANGED_FILES_TMP" $PYTHON_BIN -m code_review.main diff 2>&1) || true

# Cleanup
rm -f "$CHANGED_FILES_TMP"
echo "$result"

# Check for critical issues - exit with error if found
if echo "$result" | grep -q "Critical.*[1-9]"; then
    echo ""
    echo "❌ Critical issues found. Please fix them before committing."
    exit 1
fi

# Check exit code from code-review
if [ $? -eq 1 ]; then
    echo ""
    echo "❌ Code review failed. Please check the output above."
    exit 1
fi

echo ""
echo "✅ Code review passed!"

exit 0
'''
    click.echo(hook_script)


if __name__ == "__main__":
    cli()
