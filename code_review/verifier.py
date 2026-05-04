"""Verify and score code review results."""
import json
import re
from typing import List, Dict, Any


class Verifier:
    """Verify and deduplicate review results."""

    def verify(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse and verify LLM output."""
        issues = []

        # Try to extract JSON
        try:
            # Find JSON block
            match = re.search(r"```json\s*(.*?)\s*```", raw_output, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                # Try direct JSON parse
                data = json.loads(raw_output)

            issues = data.get("issues", [])
        except (json.JSONDecodeError, AttributeError):
            # If JSON parsing fails, try to parse line by line
            issues = self._parse_fallback(raw_output)

        # Deduplicate
        seen = set()
        unique_issues = []
        for issue in issues:
            key = (issue.get("file", ""), issue.get("line", ""), issue.get("title", ""))
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        # Filter low confidence
        filtered = [i for i in unique_issues if "?" not in i.get("title", "")]

        return filtered

    def _parse_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Fallback parsing when JSON fails."""
        issues = []
        lines = text.split("\n")

        current_issue = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for severity markers
            if "critical" in line.lower():
                current_issue["severity"] = "critical"
            elif "warning" in line.lower() or "suggestion" in line.lower():
                if "severity" not in current_issue:
                    current_issue["severity"] = "warning"
            elif "file:" in line.lower() or line.startswith("-"):
                if current_issue:
                    issues.append(current_issue)
                current_issue = {}

        if current_issue:
            issues.append(current_issue)

        return issues


class Scorer:
    """Score code review results."""

    CRITICAL_WEIGHT = -15
    WARNING_WEIGHT = -5
    SUGGESTION_WEIGHT = -1
    BASE_SCORE = 100

    def score(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate score for review."""
        critical_count = sum(1 for i in issues if i.get("severity") == "critical")
        warning_count = sum(1 for i in issues if i.get("severity") == "warning")
        suggestion_count = sum(1 for i in issues if i.get("severity") == "suggestion")

        total_deduction = (
            critical_count * self.CRITICAL_WEIGHT
            + warning_count * self.WARNING_WEIGHT
            + suggestion_count * self.SUGGESTION_WEIGHT
        )

        score = max(0, self.BASE_SCORE + total_deduction)

        # Determine rating
        if score >= 90:
            rating = "⭐⭐⭐⭐⭐"
            verdict = "优秀，建议直接合并"
        elif score >= 75:
            rating = "⭐⭐⭐⭐"
            verdict = "良好，小问题修复后可合并"
        elif score >= 60:
            rating = "⭐⭐⭐"
            verdict = "一般，需要较大改进"
        elif score >= 40:
            rating = "⭐⭐"
            verdict = "较差，建议大幅重构"
        else:
            rating = "⭐"
            verdict = "不合格，建议重新提交"

        return {
            "score": score,
            "rating": rating,
            "verdict": verdict,
            "critical": critical_count,
            "warning": warning_count,
            "suggestion": suggestion_count,
        }
