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

clean:
	rm -rf ve .tox .coverage coverage.xml
