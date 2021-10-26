DEFAULT_GOAL := help
PROJECT=crashstats_tools
BLACKVERSION=py37

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:/'

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist ${PROJECT}.egg-info .tox .pytest-cache
	rm -rf docs/_build/*
	find ${PROJECT}/ tests/ -name __pycache__ | xargs rm -rf
	find ${PROJECT}/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=${BLACKVERSION} ${PROJECT} tests setup.py
	flake8 ${PROJECT} tests

.PHONY: test
test:  ## Run tests
	tox

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install '.[dev]'
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/
