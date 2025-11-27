#!/bin/bash
# Pre-commit hook for code quality checks
# Install: cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

echo "Running pre-commit checks..."

# Run ruff linter
echo "→ Checking with ruff..."
.venv/bin/ruff check . --fix

# Run black formatter
echo "→ Formatting with black..."
.venv/bin/black . --quiet --force-exclude 'core/consumers_fixed.py'

# Run tests
echo "→ Running tests..."
.venv/bin/python -m pytest tests/test_signatures_api.py tests/test_reports_api.py tests/test_performance_queries.py -q

echo "✓ All checks passed!"
