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

.. image:: https://api.codeclimate.com/v1/badges/9c462255ca85b7f77de8/maintainability
   :target: https://codeclimate.com/github/Shoobx/shoobx.rml2odt/maintainability
   :alt: Maintainability

This library implements a converter from Reportlabs RML format to
Libreoffices/Open Document Formats ODT format utilizing the ``z3c.rml``
parser and ``odfpy`` library.

It's developed by Shoobx (https://shoobx.com) but is open source, and
we are happy to accept outside contributions. See DEVELOPMENT.rst for more
information.


Installing
==========

Install with::

    $ pip install shoobx.rml2odt


Usage
=====

There is three ways of using shoobx.rml2odt.


From the command line
---------------------

Installing shoobx.rml2odt will install a script that can be used from the
command line::

   rml2odt <infile> <outfile>


Converting files from Python
----------------------------

You can import shoobx.rml2odt as a library and convert files from Python::

    >>> from shoobx.rml2odt import rml2odt
    >>> rml2odt.convertFile(infilepath, outfilepath)

which will convert the file at infilepath and create the ODT file at
outfilepath.


Converting an RML string in Python
----------------------------------

If your RML data isn't in a file, but is held in a string, you can import
shoobx.rml2odt as a library and convert text data from Python::

    >>> from shoobx.rml2odt import rml2odt
    >>> odt_data = rml2odt.convertFile(infilepath, outfilepath)
    >>> with open(outputfile, 'wb') as output:
    ...     output.write(odt_data)

