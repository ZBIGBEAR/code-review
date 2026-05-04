"""Output formatter for code review results."""
import json
from pathlib import Path
from datetime import datetime


def format_report(issues: list, score_info: dict, commit_info: dict = None) -> str:
    """Format review results as a readable text report."""
    lines = []
    lines.append("=" * 50)
    lines.append("📋 Code Review Report")
    lines.append("=" * 50)

    if commit_info:
        lines.append(f"\n📦 Commit: {commit_info.get('sha', 'N/A')[:8]}")
        lines.append(f"👤 Author: {commit_info.get('author', 'N/A')}")
        lines.append(f"📝 Subject: {commit_info.get('subject', 'N/A')}")

    lines.append(f"\n📊 综合评分：{score_info['score']}/100 {score_info['rating']}")
    lines.append(f"\n🔴 Critical: {score_info['critical']}")
    lines.append(f"🟡 Warning: {score_info['warning']}")
    lines.append(f"🟢 Suggestion: {score_info['suggestion']}")

    if issues:
        # Group by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        suggestion_issues = [i for i in issues if i.get("severity") == "suggestion"]

        if critical_issues:
            lines.append("\n" + "=" * 50)
            lines.append("🔴 Critical Issues")
            lines.append("=" * 50)
            for issue in critical_issues:
                lines.append(_format_issue(issue))

        if warning_issues:
            lines.append("\n" + "=" * 50)
            lines.append("🟡 Warning Issues")
            lines.append("=" * 50)
            for issue in warning_issues:
                lines.append(_format_issue(issue))

        if suggestion_issues:
            lines.append("\n" + "=" * 50)
            lines.append("🟢 Suggestions")
            lines.append("=" * 50)
            for issue in suggestion_issues:
                lines.append(_format_issue(issue))
    else:
        lines.append("\n✅ 没有发现问题，代码看起来不错！")

    lines.append("\n" + "=" * 50)
    lines.append(f"✅ {score_info['verdict'] or '需要人工审查'}")
    lines.append("=" * 50)

    return "\n".join(lines)


def _format_issue(issue: dict) -> str:
    """Format a single issue."""
    lines = []
    file_path = issue.get("file", "unknown")
    line = issue.get("line", "?")
    title = issue.get("title", "No title")
    description = issue.get("description", "")
    suggestion = issue.get("suggestion", "")

    lines.append(f"\n• {file_path}:{line} - {title}")
    if description:
        lines.append(f"  说明：{description}")
    if suggestion:
        lines.append(f"  建议：{suggestion}")

    return "\n".join(lines)


def format_json(issues: list, score_info: dict) -> str:
    """Format results as JSON."""
    return json.dumps({
        "score": score_info["score"],
        "rating": score_info["rating"],
        "verdict": score_info["verdict"],
        "summary": {
            "critical": score_info["critical"],
            "warning": score_info["warning"],
            "suggestion": score_info["suggestion"],
        },
        "issues": issues,
    }, ensure_ascii=False, indent=2)


def format_markdown(issues: list, score_info: dict, commit_info: dict = None,
                   changed_files: list = None, pr_url: str = None) -> str:
    """Format results as markdown report."""
    lines = []
    lines.append("# Code Review Report")
    lines.append("")
    lines.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    if pr_url:
        lines.append(f"**PR**: {pr_url}")
        lines.append("")

    if commit_info:
        lines.append(f"**Commit**: `{commit_info.get('sha', 'N/A')[:8]}`")
        lines.append(f"**作者**: {commit_info.get('author', 'N/A')}")
        lines.append(f"**主题**: {commit_info.get('subject', 'N/A')}")
        lines.append("")

    if changed_files:
        lines.append("## 📝 变更文件")
        lines.append("")
        for f in changed_files:
            lines.append(f"- `{f}`")
        lines.append("")

    lines.append(f"## 📊 综合评分：{score_info['score']}/100 {score_info['rating']}")
    lines.append("")
    lines.append(f"- 🔴 Critical: {score_info['critical']}")
    lines.append(f"- 🟡 Warning: {score_info['warning']}")
    lines.append(f"- 🟢 Suggestion: {score_info['suggestion']}")
    lines.append("")

    if issues:
        lines.append("## 问题详情")
        lines.append("")

        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        suggestion_issues = [i for i in issues if i.get("severity") == "suggestion"]

        if critical_issues:
            lines.append("### 🔴 Critical Issues")
            lines.append("")
            for issue in critical_issues:
                lines.append(_format_markdown_issue(issue))
            lines.append("")

        if warning_issues:
            lines.append("### 🟡 Warning Issues")
            lines.append("")
            for issue in warning_issues:
                lines.append(_format_markdown_issue(issue))
            lines.append("")

        if suggestion_issues:
            lines.append("### 🟢 Suggestions")
            lines.append("")
            for issue in suggestion_issues:
                lines.append(_format_markdown_issue(issue))
            lines.append("")
    else:
        lines.append("## ✅ 没有发现问题，代码看起来不错！")
        lines.append("")
        lines.append(f"**结论**: 优秀，建议直接合并")
    lines.append("")

    return "\n".join(lines)


def _format_markdown_issue(issue: dict) -> str:
    """Format a single issue as markdown."""
    lines = []
    file_path = issue.get("file", "unknown")
    line = issue.get("line", "?")
    title = issue.get("title", "No title")
    description = issue.get("description", "")
    suggestion = issue.get("suggestion", "")
    category = issue.get("category", "")

    lines.append(f"**{file_path}:{line}** - {title}")
    lines.append("")
    lines.append(f"- 分类: {category}")
    if description:
        lines.append(f"- 说明: {description}")
    if suggestion:
        lines.append(f"- 建议: {suggestion}")
    lines.append("")

    return "\n".join(lines)


def save_report(issues: list, score_info: dict, commit_info: dict = None,
                changed_files: list = None, pr_url: str = None,
                output_dir: str = "reports") -> str:
    """Save review report as markdown file to reports directory.

    Returns the path to the saved report.
    """
    report_dir = Path(output_dir)
    report_dir.mkdir(exist_ok=True)

    # Generate filename based on commit sha or timestamp
    if commit_info and commit_info.get("sha"):
        sha = commit_info["sha"][:8]
        filename = f"review_{sha}.md"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_{timestamp}.md"

    report_path = report_dir / filename
    markdown_content = format_markdown(issues, score_info, commit_info, changed_files, pr_url)
    report_path.write_text(markdown_content, encoding="utf-8")

    return str(report_path)
