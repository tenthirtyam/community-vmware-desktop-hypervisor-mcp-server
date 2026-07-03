# Copyright (c) Ryan Johnson
# SPDX-License-Identifier: MIT

VENV ?= .venv
BOOTSTRAP_PYTHON ?= $(shell \
	if command -v python3.12 >/dev/null 2>&1; then \
		command -v python3.12; \
	elif command -v python3.13 >/dev/null 2>&1; then \
		command -v python3.13; \
	elif command -v python3.11 >/dev/null 2>&1; then \
		command -v python3.11; \
	else \
		command -v python3; \
	fi)
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
DOCS := $(PYTHON) -m properdocs
DOCS_PORT ?= 8000
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
MYPY := $(PYTHON) -m mypy
DEV_STAMP := $(VENV)/.dev-installed
DOCS_STAMP := $(VENV)/.docs-installed
PRE_COMMIT_STAMP := $(VENV)/.pre-commit-installed

.PHONY: help venv install install-cursor install-dev install-docs install-pre-commit install-vscode \
	uninstall uninstall-pre-commit \
	lint format typecheck test test-cov test-e2e test-e2e-capabilities check coverage-gate pre-commit \
	build discover \
	docs docs-serve clean

help:
	@echo "Available commands:"
	@echo "  make venv                  - Create the virtual environment"
	@echo "  make install               - Install the package"
	@echo "  make install-cursor        - Create or update the Cursor MCP configuration"
	@echo "  make install-dev           - Install development dependencies"
	@echo "  make install-docs          - Install documentation dependencies"
	@echo "  make install-pre-commit    - Install the pre-commit hook"
	@echo "  make install-vscode        - Create or update the VS Code MCP configuration"
	@echo "  make uninstall             - Remove the virtual environment"
	@echo "  make uninstall-pre-commit  - Remove the pre-commit hook"
	@echo "  make lint                  - Run Ruff checks"
	@echo "  make format                - Format code and apply Ruff fixes"
	@echo "  make typecheck             - Run mypy"
	@echo "  make test                  - Run unit tests"
	@echo "  make test-cov              - Run unit tests with coverage"
	@echo "  make test-e2e              - Run live E2E tests"
	@echo "  make test-e2e-capabilities - Run live E2E capability checks"
	@echo "  make check                 - Run lint, type checks, tests, and coverage gate"
	@echo "  make coverage-gate         - Check the coverage threshold"
	@echo "  make pre-commit            - Run pre-commit hooks"
	@echo "  make build                 - Build the wheel and sdist"
	@echo "  make discover              - Regenerate manifest artifacts from vmcli"
	@echo "  make docs                  - Build the documentation content"
	@echo "  make docs-serve            - Serve the documentation site"
	@echo "  make clean                 - Remove generated artifacts"

venv: $(PYTHON)

$(PYTHON):
	$(BOOTSTRAP_PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e .

install-dev: venv
install-dev: $(DEV_STAMP) $(PRE_COMMIT_STAMP)

$(DEV_STAMP): $(PYTHON) pyproject.toml
	$(PIP) install -e ".[dev]"
	@touch $(DEV_STAMP)

install-docs: $(DOCS_STAMP)

$(DOCS_STAMP): $(PYTHON) pyproject.toml
	@if ! $(PIP) --version >/dev/null 2>&1; then \
		echo "Rebuilding broken virtual environment at $(VENV)"; \
		rm -rf $(VENV); \
		$(MAKE) venv; \
	fi
	$(PIP) install -e ".[docs]"
	@touch $(DOCS_STAMP)

install-pre-commit: $(PRE_COMMIT_STAMP)

$(PRE_COMMIT_STAMP): $(DEV_STAMP)
	$(PYTHON) -m pre_commit install
	@touch $(PRE_COMMIT_STAMP)

install-cursor: install
	@$(PYTHON) -c "import community_vmware_desktop_hypervisor_mcp_server" || \
		(echo "Package not importable: run: make install" && exit 1)
	@$(PYTHON) scripts/write_mcp_config.py cursor .cursor/mcp.json
	@echo "Enable in Cursor under 'Cursor Settings > Tools & MCPs'."

install-vscode: install
	@$(PYTHON) -c "import community_vmware_desktop_hypervisor_mcp_server" || \
		(echo "Package not importable: run: make install" && exit 1)
	@$(PYTHON) scripts/write_mcp_config.py vscode .vscode/mcp.json
	@echo "Start in VS Code under 'MCP: List Servers'."

uninstall: uninstall-pre-commit
	@if [ -d "$(VENV)" ]; then \
		rm -rf $(VENV); \
	else \
		echo "No virtual environment found at $(VENV)"; \
	fi

uninstall-pre-commit:
	@if [ -x "$(PYTHON)" ]; then \
		$(PYTHON) -m pre_commit uninstall >/dev/null 2>&1 || true; \
	elif [ -f ".git/hooks/pre-commit" ]; then \
		rm -f .git/hooks/pre-commit; \
	fi
	@rm -f $(PRE_COMMIT_STAMP)

lint: install-dev
	$(RUFF) check src tests

format: install-dev
	$(RUFF) format src tests
	$(RUFF) check --fix src tests

typecheck: install-dev
	$(MYPY) src/community_vmware_desktop_hypervisor_mcp_server

test: install-dev
	PYTHONPATH=src $(PYTEST)

test-cov: install-dev
	PYTHONPATH=src $(PYTEST) --cov --cov-report=html --cov-report=term

test-e2e: install-dev
	@test -n "$(VMCLI_E2E_VMX_PATH)" || (echo "Set VMCLI_E2E_VMX_PATH to your .vmx" && exit 1)
	VDH_E2E=1 PYTHONPATH=src $(PYTEST) -m e2e -v --no-cov

test-e2e-capabilities: install-dev
	@test -n "$(VMCLI_E2E_VMX_PATH)" || (echo "Set VMCLI_E2E_VMX_PATH to your .vmx" && exit 1)
	PYTHONPATH=src $(PYTHON) scripts/e2e_mcp_capabilities.py --vmx "$(VMCLI_E2E_VMX_PATH)"

check: lint typecheck test coverage-gate

coverage-gate: install-dev
	PYTHONPATH=src $(PYTHON) scripts/coverage_gate.py

pre-commit: install-dev
	$(PYTHON) -m pre_commit run --all-files

build:
	$(PIP) install build
	$(PYTHON) -m build

verify-version:
	@$(PYTHON) -c "\
import json, tomllib, sys; \
pyp = tomllib.load(open('pyproject.toml','rb'))['project']['version']; \
srv = json.load(open('server.json')); \
errors = []; \
errors += [f'server.json \".version\" ({srv[\"version\"]!r}) != pyproject.toml ({pyp!r})'] if srv['version'] != pyp else []; \
errors += [f'server.json \".packages[0].version\" ({srv[\"packages\"][0][\"version\"]!r}) != pyproject.toml ({pyp!r})'] if srv['packages'][0]['version'] != pyp else []; \
[print(f'ERROR: {e}', file=sys.stderr) for e in errors] or print(f'OK: all versions are {pyp!r}'); \
sys.exit(bool(errors)) \
"

discover:
	PYTHONPATH=src $(PYTHON) scripts/discover_vmcli.py

docs: install-docs
	$(DOCS) build

docs-serve: install-docs
	@pids="$$(lsof -tiTCP:$(DOCS_PORT) -sTCP:LISTEN 2>/dev/null || true)"; \
	for pid in $$pids; do \
		echo "Stopping existing server on port $(DOCS_PORT): $$pid"; \
		kill "$$pid" 2>/dev/null || true; \
	done; \
	for attempt in 1 2 3 4 5 6 7 8 9 10; do \
		if ! lsof -tiTCP:$(DOCS_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 1; \
	done; \
	if lsof -tiTCP:$(DOCS_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "Force stopping server on port $(DOCS_PORT)"; \
		lsof -tiTCP:$(DOCS_PORT) -sTCP:LISTEN | xargs kill -9 2>/dev/null || true; \
	fi
	$(DOCS) serve --open --livereload -a 127.0.0.1:$(DOCS_PORT) -w ./

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	rm -rf site .site
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
