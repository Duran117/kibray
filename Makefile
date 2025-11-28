PYTHON=.venv/bin/python
PIP=.venv/bin/pip

.PHONY: check test audit

check:
	$(PYTHON) manage.py check
	$(PIP) install ruff bandit || true
	.venv/bin/ruff check . || true
	.venv/bin/bandit -r core -f txt || true

test:
	$(PYTHON) -m pytest --maxfail=1 -q

coverage:
	$(PYTHON) -m coverage run -m pytest
	$(PYTHON) -m coverage xml -o reports/coverage.xml || true
	$(PYTHON) -m coverage html -d reports/coverage_html || true

audit: check test coverage
