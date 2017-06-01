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

Step 2: Download Python Build 2.7.13 here.

Step 3: Install Libreoffice here.

Step 4: Open your terminal and type the following commands in the terminal. (All commands meant to be inputted in the terminal will be bolded and indented)

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

Step 11: Install homebrew with the following command:
/usr/bin/ruby -e “$(curl -fsSL https://raw.githibusercontent.com/Homebrew/install/master/install)”

Step 12: Install unoconv with brew:
brew install unoconv

Step 13: Install ghostscript with brew
brew install ghostscript

Step 14: Navigate to test_rml2docx.py file:
open ./shoobx.rml2docx/src/shoobx/rml2docx/tests/test_rml2docx.py
In the return statement of the function “def unoconv_command(path, opath=None):”
Replace '/usr/bin/unoconv' with  '/usr/local/bin/unoconv'
Replace ‘/usr/bin/python3’ with ‘/Applications/LibreOffice.app/Contents/program/python’

Step 15: Run the demo file
sudo ve/bin/tox -e py27
