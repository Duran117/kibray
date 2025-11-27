# Contributing to Kibray

Thank you for your interest in contributing to Kibray! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Collaborate openly and transparently
- Prioritize code quality and maintainability

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone <your-fork-url>
cd kibray
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

---

## Development Workflow

### Branch Naming Conventions

- **Features**: `feature/descriptive-name`
- **Bug Fixes**: `fix/bug-description`
- **Refactoring**: `refactor/what-changed`
- **Documentation**: `docs/topic`
- **Tests**: `test/what-tested`

### Commit Message Format

Use clear, descriptive commit messages:

```
<type>: <subject>

<optional body>

<optional footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `test`: Test additions/changes
- `docs`: Documentation updates
- `style`: Code formatting (no logic change)
- `perf`: Performance improvements

**Examples**:
```
feat: add digital signature verification API

- Create Signature model with hash validation
- Add SignatureViewSet with verify action
- Include tests for create/verify/permissions

Closes #123
```

```
fix: resolve N+1 query in budget_overview endpoint

Changed from prefetch_related with loop aggregation
to single annotate query with Sum.

Performance: 14 queries → 5 queries for 10 projects
```

---

## Code Standards

### Python Style Guide

We use **black** (formatter) and **ruff** (linter) to enforce code quality:

```bash
# Before committing, run:
ruff check . --fix
black .
```

### Key Standards

- **Line Length**: 120 characters (configured in pyproject.toml)
- **Imports**: Organized with ruff's isort (stdlib → third-party → local)
- **Type Hints**: Use for new functions (optional but encouraged)
- **Docstrings**: Use for public APIs and complex functions

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ProjectViewSet`)
- **Functions/Methods**: `snake_case` (e.g., `budget_overview`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `STATUS_CHOICES`)
- **Private Methods**: Prefix with `_` (e.g., `_sync_payment_flags`)

### Django-Specific Guidelines

- Use `get_object_or_404()` for single object retrieval
- Prefer `select_related()` and `prefetch_related()` to avoid N+1 queries
- Add database indexes for frequently queried fields
- Use `models.Q()` for complex queries
- Always validate user input in forms/serializers

---

## Testing Requirements

### Test Coverage

- **Minimum**: All new features must have tests
- **Target**: >90% code coverage for production readiness
- **Current**: 50% baseline (improving)

### Writing Tests

```python
# tests/test_your_feature.py
import pytest
from django.contrib.auth import get_user_model
from core.models import YourModel

User = get_user_model()

@pytest.mark.django_db
class TestYourFeature:
    def test_feature_works(self):
        """Test that your feature behaves correctly"""
        user = User.objects.create_user(username="test", password="pass123")
        obj = YourModel.objects.create(user=user, field="value")
        
        assert obj.field == "value"
        assert obj.user == user
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_your_feature.py

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run only failed tests from last run
pytest --lf
```

### Test Types to Include

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test interactions between components
3. **API Tests**: Test REST endpoints (auth, permissions, responses)
4. **Performance Tests**: Validate query counts for N+1 prevention
5. **Security Tests**: Test negative cases (403, 404, 405)

### Pre-commit Checklist

Before pushing, ensure:
- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black .`)
- [ ] Code is linted (`ruff check . --fix`)
- [ ] Coverage hasn't decreased significantly
- [ ] No new warnings introduced

**Optional**: Install pre-commit hook:
```bash
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Pull Request Process

### 1. Ensure Quality

- All tests pass
- Code is formatted and linted
- Coverage is maintained or improved
- Documentation is updated if needed

### 2. Create Pull Request

**Title Format**: `<type>: <brief description>`

**Example**: `feat: add CSV export for project cost reports`

**PR Description Template**:
```markdown
## Description
Brief summary of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe tests added/modified

## Checklist
- [ ] Tests pass locally
- [ ] Code is formatted (black) and linted (ruff)
- [ ] Documentation updated
- [ ] No sensitive data committed

## Related Issues
Closes #123
```

### 3. Code Review

- Address reviewer feedback promptly
- Keep discussions focused and professional
- Update PR based on suggestions
- Re-request review after changes

### 4. Merge Criteria

PRs are merged when:
- ✅ All CI checks pass (GitHub Actions)
- ✅ Code review approved by maintainer
- ✅ No merge conflicts
- ✅ Documentation updated if applicable

---

## Performance Guidelines

### Query Optimization

Always check query counts for list endpoints:

```python
# Use django-debug-toolbar or pytest-django
from django.test.utils import CaptureQueriesContext
from django.db import connection

def test_query_count(api_client, user):
    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get('/api/endpoint/')
    
    # Assert reasonable query count
    assert len(ctx.captured_queries) <= 5
```

### N+1 Prevention

Use `select_related()` for foreign keys:
```python
# Bad
projects = Project.objects.all()
for p in projects:
    print(p.client.name)  # N+1 queries

# Good
projects = Project.objects.select_related('client')
```

Use `prefetch_related()` for reverse relationships:
```python
# Bad
projects = Project.objects.all()
for p in projects:
    print(p.tasks.count())  # N+1 queries

# Good
projects = Project.objects.prefetch_related('tasks')
```

Use `annotate()` for aggregations:
```python
# Bad
projects = Project.objects.prefetch_related('expenses')
for p in projects:
    total = p.expenses.aggregate(total=Sum('amount'))['total']  # N queries

# Good
from django.db.models import Sum
projects = Project.objects.annotate(
    expense_total=Sum('expenses__amount')
)
```

---

## Security Best Practices

### Authentication & Authorization

- Always check `request.user.is_authenticated`
- Use `@login_required` for view-based auth
- Use DRF's `IsAuthenticated` permission for APIs
- Validate ownership for update/delete operations

```python
# Example: Restrict updates to owner
def perform_update(self, serializer):
    if serializer.instance.user != self.request.user:
        raise PermissionDenied("Can only update your own objects")
    serializer.save()
```

### Input Validation

- Never trust user input
- Use Django forms/serializers for validation
- Sanitize file uploads
- Validate file types and sizes

### Sensitive Data

- Never commit secrets (API keys, passwords)
- Use environment variables for configuration
- Add sensitive files to `.gitignore`

---

## Documentation Standards

### Code Documentation

- Add docstrings to public functions/classes
- Explain complex logic with inline comments
- Document API endpoints in docstrings

```python
def budget_overview(self, request):
    """
    GET /api/v1/projects/budget-overview/
    
    Returns budget vs actual spending for all projects.
    
    Response:
        [
            {
                "id": 1,
                "name": "Project A",
                "budget_total": "10000.00",
                "expense_total": "7500.00",
                "budget_remaining": "2500.00"
            }
        ]
    
    Performance: Uses single annotate query (≤5 total queries).
    """
```

### README Updates

Update README.md when:
- Adding major features
- Changing setup process
- Adding new dependencies
- Updating version numbers

---

## Questions or Issues?

- Check existing [documentation](README.md)
- Search [open issues](https://github.com/your-org/kibray/issues)
- Create a new issue if needed

---

Thank you for contributing to Kibray! 🎨
