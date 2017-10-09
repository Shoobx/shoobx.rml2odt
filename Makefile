PYTHON = python2.7

all: ve/bin/unoconv env

ve:
	virtualenv -p $(PYTHON) ve
	ve/bin/pip install -e .[test]

ve/bin/unoconv: | ve
	ve/bin/pip install ./ci/unoconv-0.7.tar.gz

env:
	echo /usr/bin/python3 > env

.PHONY: test
test: ve/bin/unoconv
	ve/bin/zope-testrunner -vpc1 --all --test-path=${PWD}/src

clean:
	rm -rf ve .tox .coverage coverage.xml
