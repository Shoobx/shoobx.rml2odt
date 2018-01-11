PYTHON = python2.7

all: env ve

ve:
	virtualenv -p $(PYTHON) ve
	ve/bin/pip install -e .[test]

env:
	echo /usr/bin/python3 > env

.PHONY: test
test: ve
	ve/bin/zope-testrunner -vpc1 --all --test-path=${PWD}/src

.PHONY: coverage
coverage: ve
	bin/coverage run ve/bin/zope-testrunner -vpc1 --all --test-path=${PWD}/src
	bin/coverage html

clean:
	rm -rf ve .tox .coverage coverage.xml
