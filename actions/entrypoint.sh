#!/bin/bash
# Code Review GitHub Actions Entrypoint
# Usage: This script is called by the GitHub Action

set -e

echo "🔍 Starting Code Review..."

# Check if PR URL is provided
if [ -z "$INPUT_PR_URL" ]; then
    echo "❌ PR_URL input is required"
    exit 1
fi

# Install code-review if not already installed
if ! command -v code-review &> /dev/null; then
    echo "📦 Installing code-review..."
    pip install -e /action_path/
fi

# Run code review
echo "📝 Reviewing PR: $INPUT_PR_URL"
result=$(code-review pr "$INPUT_PR_URL" 2>&1) || true

echo "$result"

# Write output to GitHub Actions output
echo "REVIEW_RESULT=$result" >> $GITHUB_OUTPUT

# Exit with appropriate code
if echo "$result" | grep -q "Critical:\s*[1-9]"; then
    echo ""
    echo "❌ Critical issues found. PR needs fixes before merge."
    exit 1
fi

echo ""
echo "✅ Code review completed."

exit 0
