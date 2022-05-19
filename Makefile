.DEFAULT_GOAL := all
isort = isort ot2util examples test
black = black --target-version py37 ot2util examples test

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: lint
lint:
	$(black) --check --diff
	flake8 ot2util/ examples/ test/
	#pylint ot2util/ #examples/ test/
	#pydocstyle ot2util/


.PHONY: mypy
mypy:
	mypy --config-file setup.cfg --package ot2util
	mypy --config-file setup.cfg ot2util/
	mypy --config-file setup.cfg examples/

.PHONY: all
all: format lint mypy