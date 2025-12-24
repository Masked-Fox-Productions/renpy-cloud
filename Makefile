.PHONY: help install test lint format clean deploy deploy-infra run-example

help:
	@echo "renpy-cloud development commands:"
	@echo ""
	@echo "  make install        Install package and dev dependencies"
	@echo "  make test           Run all tests with coverage"
	@echo "  make lint           Run linters (flake8, mypy)"
	@echo "  make format         Format code with black"
	@echo "  make clean          Remove build artifacts and cache"
	@echo "  make deploy-infra   Deploy AWS infrastructure"
	@echo "  make remove-infra   Remove AWS infrastructure"
	@echo "  make package        Build distribution packages"
	@echo ""

install:
	pip install -e ".[dev]"

test:
	pytest --cov=renpy_cloud --cov-report=term-missing --cov-report=html

lint:
	flake8 renpy_cloud tests
	mypy renpy_cloud

format:
	black renpy_cloud tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete

deploy-infra:
	cd infra && serverless deploy

remove-infra:
	cd infra && serverless remove

package:
	python setup.py sdist bdist_wheel

publish: package
	twine upload dist/*

# Development helpers
dev-setup: install
	pip install twine wheel

watch-tests:
	pytest-watch

# Infrastructure helpers
infra-logs:
	cd infra && serverless logs -f syncPlan -t

infra-info:
	cd infra && serverless info

