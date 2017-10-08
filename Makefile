PYTHON = python2.7
OFFICE_VERSION = 5.3.1.2
OFFICE_2DVERSION := $(shell echo $(OFFICE_VERSION) | cut -c 1-3)
UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
  PYTHON_OFFICE_BIN = '/opt/libreoffice$(OFFICE_2DVERSION)/program/python'
endif
ifeq ($(UNAME), Darwin)
  PYTHON_OFFICE_BIN = '/Applications/LibreOffice.app/Contents/MacOS/python'
endif

all: ve/bin/unoconv ve/bin/zope-testrunner env

ve:
	virtualenv -p $(PYTHON) ve
	ve/bin/pip install -e .[test]

ve/bin/zope-testrunner: | ve
	ve/bin/pip install zope.testrunner

ve/bin/unoconv: | ve
	ve/bin/pip install ./ci/unoconv-0.7.tar.gz

env:
	echo $(PYTHON_OFFICE_BIN) > env

.PHONY: install-office
install-office: $(PYTHON_OFFICE_BIN)

$(PYTHON_OFFICE_BIN):
	sudo VERSION=$(OFFICE_VERSION) bash ci/linux.bash
	sudo VERSION=$(OFFICE_VERSION) bash ci/osx.bash

.PHONY: test
test: ve/bin/unoconv ve/bin/zope-testrunner
	ve/bin/zope-testrunner -vpc1 --all --test-path=${PWD}/src

clean:
	rm -rf ve .tox .coverage coverage.xml
