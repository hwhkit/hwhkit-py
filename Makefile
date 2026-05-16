.DEFAULT_GOAL := help
.PHONY: help dev install test test-unit test-integration test-e2e test-cov lint format typecheck docs docs-serve build clean security

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## sync dev dependencies
	uv sync --extra dev --extra docs --extra security

dev: install ## prep dev env + pre-commit hooks
	uv run pre-commit install

test: ## run all unit tests
	uv run pytest tests/unit -v

test-unit: ## alias for test
	$(MAKE) test

test-integration: ## run integration tests (requires Docker)
	uv run pytest tests/integration -v -m integration

test-e2e: ## run e2e tests
	uv run pytest tests/e2e -v -m e2e

test-cov: ## run unit tests with coverage report
	uv run pytest tests/unit --cov=hwhkit --cov-report=term-missing --cov-report=html

lint: ## run ruff check
	uv run ruff check hwhkit tests
	uv run ruff format --check hwhkit tests

format: ## auto-format with ruff
	uv run ruff format hwhkit tests
	uv run ruff check --fix hwhkit tests

typecheck: ## run mypy --strict
	uv run mypy hwhkit

docs: ## build docs site
	uv run mkdocs build --strict

docs-serve: ## serve docs locally at http://127.0.0.1:8000
	uv run mkdocs serve

build: ## build wheel + sdist
	uv build

clean: ## remove build artifacts
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

security: ## run security scanners
	uv run bandit -r hwhkit -q
	uv run pip-audit
