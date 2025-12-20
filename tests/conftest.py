from unittest import mock

import pytest

# Auto-mark all tests with django_db so legacy tests without explicit marks can access the database.
# This avoids RuntimeError from pytest-django enforcing DB access restrictions on unmarked tests.
# If certain tests should NOT hit the DB, they can add @pytest.mark.no_db and we can refine logic later.


@pytest.fixture
def mocker():
    """Lightweight stand-in for pytest-mock's mocker fixture.

    Provides .patch that auto-starts patches and cleans them up after the test.
    """

    active_patches = []

    class _PatchProxy:
        def __init__(self, owner):
            self.owner = owner

        def __call__(self, target, *args, **kwargs):
            return self.owner._patch(target, *args, **kwargs)

        def object(self, target, attribute, *args, **kwargs):
            return self.owner._patch_object(target, attribute, *args, **kwargs)

    class _Mocker:
        def __init__(self):
            self.patch = _PatchProxy(self)

        def _patch(self, target, *args, **kwargs):  # type: ignore[func-returns-value]
            p = mock.patch(target, *args, **kwargs)
            started = p.start()
            active_patches.append(p)
            return started

        def _patch_object(self, target, attribute, *args, **kwargs):
            p = mock.patch.object(target, attribute, *args, **kwargs)
            started = p.start()
            active_patches.append(p)
            return started

        def stopall(self):
            for p in active_patches:
                p.stop()
            active_patches.clear()

    helper = _Mocker()
    yield helper
    helper.stopall()


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "django_db" not in item.keywords:
            item.add_marker(pytest.mark.django_db)
