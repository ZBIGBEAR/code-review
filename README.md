# Code Review

Multi-agent code review system with LLM, supporting Git hooks and GitHub Actions.

## Features

- **LLM-powered review**: Uses Claude for intelligent code review
- **Multi-dimensional checks**: Security, Style, Performance, Testing, Documentation
- **Scoring system**: Get a score (0-100) for each code change
- **Git hooks**: Run review automatically before commit
- **GitHub Actions**: CI/CD integration

## Installation

```bash
pip install -e .
```

## Usage

### Review a GitHub PR

```bash
code-review pr https://github.com/user/repo/pull/123
```

### Review recent commits

```bash
code-review commit --commit HEAD~1
```

### Review uncommitted changes

```bash
code-review diff --base-branch main
```

### Review a specific file

```bash
code-review file path/to/file.py
```

## Git Hook Integration

Install the pre-commit hook:

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or use the built-in command:

```bash
code-review hook install
```

## GitHub Actions

Add this to your workflow file (e.g., `.github/workflows/code-review.yml`):

```yaml
name: Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install code-review
        run: pip install code-review
      - name: Run Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          code-review pr ${{ github.event.pull_request.html_url }}
```

## Environment Variables

- `ANTHROPIC_API_KEY`: Anthropic API key for Claude
- `ANTHROPIC_BASE_URL`: Anthropic API base URL (optional)
- `CLAUDE_MODEL`: Model to use (default: claude-sonnet-4-7-20250514)

## Configuration

Create a `.code-review.yaml` in your project root:

```yaml
scoring:
  critical_weight: -15
  warning_weight: -5
  suggestion_weight: -1

categories:
  - security
  - style
  - performance
  - test
  - docs
```

## License

MIT
