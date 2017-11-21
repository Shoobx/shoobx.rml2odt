================================================
``shoobx.rml2odt`` -- Conversion of RML to ODT
================================================

.. image:: https://travis-ci.org/Shoobx/shoobx.rml2odt.png?branch=master
   :target: https://travis-ci.org/Shoobx/shoobx.rml2odt

.. image:: https://coveralls.io/repos/github/Shoobx/shoobx.rml2odt/badge.svg?branch=master
   :target: https://coveralls.io/github/Shoobx/shoobx.rml2odt?branch=master

.. image:: https://img.shields.io/pypi/v/shoobx.rml2odt.svg
    :target: https://pypi.python.org/pypi/shoobx.rml2odt

.. image:: https://img.shields.io/pypi/pyversions/shoobx.rml2odt.svg
    :target: https://pypi.python.org/pypi/shoobx.rml2odt/


This library implements a converter from RML to ODT format utilizing
the ``z3c.rml`` parser and odfpy library.


MAC OSX SETUP
=============

Step 1: Update your Operating system to the latest build.

Step 2: Ensure you have Python 2.7, 3.5 or 3.6 installed by entering the following command::

    ``python --version``

Step 3: Install Libreoffice here:
        http://downloadarchive.documentfoundation.org/libreoffice/old/4.3.5.2/mac/x86_64/

Step 4: Open your terminal and type the following commands in the terminal.
        (All commands meant to be inputted in the terminal will be indented)

Step 5: Obtain access to the Shoobx GitHub account from your supervisor.

Step 6: Clone the GitHub repository with the following command::

        ``git clone https://github.com/Shoobx/shoobx.rml2odt.git``

Step 7: Install pip with the following command:
    sudo easy_install pip

Step 8: Enter the Shoobx folder with the following command:
    cd shoobx.rml2odt

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

Step 14: Install homebrew with the following command::

    /usr/bin/ruby -e “$(curl -fsSL https://raw.githibusercontent.com/Homebrew/install/master/install)”

Step 15: Install unoconv with brew with the following command::

    brew install unoconv

Step 16: Enter the following command::

    ln -s /usr/local/Cellar/unoconv/0.7/bin/unoconv /usr/local/bin/unoconv

Step 17: Install ghostscript with brew with the following command::

    brew install ghostscript

Step 18: Navigate to test_rml2odt.py file with the following command::

    ``open ./shoobx.rml2odt/src/shoobx/rml2odt/tests/test_rml2odt.py``

    In the return statement of the function ``def unoconv_command(path, opath=None):``
    Replace '/usr/bin/unoconv' with  '/usr/local/bin/unoconv'
    Replace ‘/usr/bin/python3’ with ‘/Applications/LibreOffice.app/Contents/program/python’

Step 19: Run the demo file with the following command::

    sudo tox -e py27
