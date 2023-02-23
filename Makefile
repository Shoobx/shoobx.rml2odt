PYTHON = python3.10
VIRTUALENV = ve

all: env ve

ve:
	$(PYTHON) -m venv $(VIRTUALENV); \
	$(VIRTUALENV)/bin/pip install --upgrade setuptools; \
	$(VIRTUALENV)/bin/pip install --upgrade wheel

	$(VIRTUALENV)/bin/pip install -e .[test]

env:
	echo /usr/bin/python3 > env

.PHONY: test
test: ve env
	$(VIRTUALENV)/bin/zope-testrunner -vvc1 --all --test-path=${PWD}/src

.PHONY: coverage
coverage: ve env
	$(VIRTUALENV)/bin/coverage run $(VIRTUALENV)/bin/zope-testrunner -vpc1 --all --test-path=${PWD}/src
	$(VIRTUALENV)/bin/coverage html

clean:
	rm -rf ve .tox .coverage coverage.xml
