.DEFAULT_GOAL := all
isort = isort examples
black = black --target-version py37 examples ot2util

.PHONY: format
format:
	$(black)

.PHONY: lint
lint:
	flake8 examples/ ot2util/
	$(black) --check --diff

.PHONY: mypy
mypy:
	mypy --config-file setup.cfg --package ot2util
	mypy --config-file setup.cfg ot2util/
	mypy --config-file setup.cfg examples/

.PHONY: all
all: format lint mypy