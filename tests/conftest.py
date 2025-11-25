import pytest

# Auto-mark all tests with django_db so legacy tests without explicit marks can access the database.
# This avoids RuntimeError from pytest-django enforcing DB access restrictions on unmarked tests.
# If certain tests should NOT hit the DB, they can add @pytest.mark.no_db and we can refine logic later.

def pytest_collection_modifyitems(config, items):
    for item in items:
        if 'django_db' not in item.keywords:
            item.add_marker(pytest.mark.django_db)
