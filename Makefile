.DEFAULT_GOAL := all
isort = isort examples
black = black --target-version py37 examples

.PHONY: format
format:
	$(black)

.PHONY: lint
lint:
	flake8 examples/
	$(black) --check --diff

.PHONY: mypy
mypy:
	mypy --config-file setup.cfg --package examples
	mypy --config-file setup.cfg examples/

.PHONY: all
all: format lint mypy