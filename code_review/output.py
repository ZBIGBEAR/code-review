"""Output formatter for code review results."""
from typing import List, Dict, Any


def format_report(issues: List[Dict[str, Any]], score_info: Dict[str, Any], commit_info: dict = None) -> str:
    """Format review results as a readable report."""
    lines = []
    lines.append("=" * 50)
    lines.append("📋 Code Review Report")
    lines.append("=" * 50)

    if commit_info:
        lines.append(f"\n📦 Commit: {commit_info.get('sha', 'N/A')[:8]}")
        lines.append(f"👤 Author: {commit_info.get('author_name', 'N/A')}")
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
    lines.append(f"✅ {score_info['verdict']}")
    lines.append("=" * 50)

    return "\n".join(lines)


def _format_issue(issue: Dict[str, Any]) -> str:
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


def format_json(issues: List[Dict[str, Any]], score_info: Dict[str, Any]) -> str:
    """Format results as JSON."""
    import json
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
