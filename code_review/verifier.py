"""Verifier and scorer for code review results."""
import json


class Scorer:
    """Score code review results."""

    CRITICAL_WEIGHT = -15
    WARNING_WEIGHT = -5
    SUGGESTION_WEIGHT = -1
    BASE_SCORE = 100

    def score(self, issues: list) -> dict:
        """Calculate score from issues list."""
        if isinstance(issues, str):
            try:
                issues = json.loads(issues)
            except json.JSONDecodeError:
                issues = []

        critical = sum(1 for i in issues if i.get("severity") == "critical")
        warning = sum(1 for i in issues if i.get("severity") == "warning")
        suggestion = sum(1 for i in issues if i.get("severity") == "suggestion")

        score = max(0, self.BASE_SCORE +
                    critical * self.CRITICAL_WEIGHT +
                    warning * self.WARNING_WEIGHT +
                    suggestion * self.SUGGESTION_WEIGHT)

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
            "critical": critical,
            "warning": warning,
            "suggestion": suggestion,
        }
