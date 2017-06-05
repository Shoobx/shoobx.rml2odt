================================================
``shoobx.rml2docx`` -- Conversion of RML to DOCX
================================================

.. image:: https://travis-ci.org/Shoobx/shoobx.rml2docx.png?branch=master
   :target: https://travis-ci.org/Shoobx/shoobx.rml2docx

.. image:: https://coveralls.io/repos/github/Shoobx/shoobx.rml2docx/badge.svg?branch=master
   :target: https://coveralls.io/github/Shoobx/shoobx.rml2docx?branch=master

.. image:: https://img.shields.io/pypi/v/shoobx.rml2docx.svg
    :target: https://pypi.python.org/pypi/shoobx.rml2docx

.. image:: https://img.shields.io/pypi/pyversions/shoobx.rml2docx.svg
    :target: https://pypi.python.org/pypi/shoobx.rml2docx/


This library implements a converter from RML to DOCX format utilizing
the ``z3c.rml`` parser.



================================================
                  MAC OSX SETUP
================================================

Step 1: Update your Operating system to the latest build.

Step 2: Ensure you have Python 2.7.13 downloaded by entering the following command: 
	python --version
If you have a different build, download Python Build 2.7.13 here : https://www.python.org/downloads/release/python-2713/.

Step 3: Install Libreoffice here: 
http://downloadarchive.documentfoundation.org/libreoffice/old/4.3.5.2/mac/x86_64/

Step 4: Open your terminal and type the following commands in the terminal. (All commands meant to be inputted in the terminal will be indented)

Step 5: Obtain access to the Shoobx GitHub account from your supervisor.

Step 6: Clone the GitHub repository with the following command:
 	git clone https://github.com/Shoobx/shoobx.rml2docx.git

Step 7: Install pip with the following command:
	sudo easy_install pip

Step 8: Enter the Shoobx folder with the following command:
	cd shoobx.rml2docx

Step 9: Install tox with the following command:
	pip install tox

Step 10: Install virtualenv with the following command:
	pip install virtualenv

Step 11: Start the virtual environment in the folder with the following command:
	virtualenv ve

Step 12: Enter the following commands:
	pip install -e “.[test]”
	pip install -e tox
	tox -e py27


Step 14: Install homebrew with the following command:
	/usr/bin/ruby -e “$(curl -fsSL https://raw.githibusercontent.com/Homebrew/install/master/install)”

Step 15: Install unoconv with brew with the following command:
	brew install unoconv

Step 16: Enter the following command:
	ln -s /usr/local/Cellar/unoconv/0.7/bin/unoconv /usr/local/bin/unoconv

Step 17: Install ghostscript with brew with the following command:
	brew install ghostscript

Step 18: Navigate to test_rml2docx.py file with the following command:
	open ./shoobx.rml2docx/src/shoobx/rml2docx/tests/test_rml2docx.py
In the return statement of the function “def unoconv_command(path, opath=None):”
Replace '/usr/bin/unoconv' with  '/usr/local/bin/unoconv'
Replace ‘/usr/bin/python3’ with ‘/Applications/LibreOffice.app/Contents/program/python’

Step 19: Run the demo file with the following command:
	sudo tox -e py27
