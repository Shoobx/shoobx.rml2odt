##############################################################################
#
# Copyright (c) 2017 Shoobx, Inc.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""RML to ODT Converter"""
import argparse
import lxml.etree
import six
import zope.interface

from shoobx.rml2odt import document, interfaces

zope.interface.moduleProvides(interfaces.IRML2ODT)


def convertString(rml, remove_encoding=True, filename=None):
    if isinstance(rml, six.string_types) and remove_encoding:
        # RML is a unicode string, but oftentimes documents declare their
        # encoding using <?xml ...>. Unfortuantely, I cannot tell lxml to
        # ignore that directive. Thus we remove it.
        if rml.startswith('<?xml'):
            rml = rml.split('\n', 1)[-1]
    root = lxml.etree.fromstring(rml)
    doc = document.Document(root)
    if filename:
        doc.filename = filename
    output = six.BytesIO()
    doc.process(output)
    output.seek(0)
    return output


def convertFile(inputfile, outputfile):
    with open(inputfile, 'rb') as rmlinput:
        root = lxml.etree.parse(rmlinput).getroot()
        doc = document.Document(root)
        doc.filename = inputfile

    with open(outputfile, 'wb') as odtoutput:
        # Create a Reportlab canvas by processing the document
        doc.process(odtoutput)


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(
            prog='rml2pdf',
            description='Converts file in RML format into ODT file.',
            epilog='Copyright (c) 2017 Shoobx, Inc.'
        )
        parser.add_argument(
            'inputfile',
            help='RML file to be processed')
        parser.add_argument(
            'outputfile', nargs='?',
            help='Output ODT file name')
        pargs = parser.parse_args()

    convertFile(pargs.inputfile, pargs.outputfile)
