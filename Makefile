DEFAULT_GOAL := help
PROJECT=crashstats_tools

.PHONY: help
help:
	@echo "Available rules:"
	@echo ""
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:/'

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist src/${PROJECT}.egg-info .tox .pytest_cache/
	rm -rf docs/_build/*
	find src tests/ -name __pycache__ | xargs rm -rf
	find src tests/ -name '*.pyc' | xargs rm -rf

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py37 --line-length=88 setup.py src tests
	tox -e py37-lint

.PHONY: test
test:  ## Run tests
	tox

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install -r requirements-dev.txt
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/
