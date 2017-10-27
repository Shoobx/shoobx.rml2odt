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
import os
import six
import sys
import zope.interface

from shoobx.rml2odt import document, interfaces

zope.interface.moduleProvides(interfaces.IRML2ODT)


def parseString(xml, removeEncodingLine=True, filename=None):
    if isinstance(xml, six.text_type) and removeEncodingLine:
        # RML is a unicode string, but oftentimes documents declare their
        # encoding using <?xml ...>. Unfortuantely, I cannot tell lxml to
        # ignore that directive. Thus we remove it.
        if xml.startswith('<?xml'):
            xml = xml.split('\n', 1)[-1]
    root = lxml.etree.fromstring(xml)
    doc = document.Document(root)
    if filename:
        doc.filename = filename
    output = six.BytesIO()
    doc.process(output)
    output.seek(0)
    return output


def go(xmlInputName, outputFileName='', outDir=None):
    if hasattr(xmlInputName, 'read'):
        # it is already a file-like object
        xmlFile = xmlInputName
        xmlInputName = 'input.rml'
    else:
        xmlFile = open(xmlInputName, 'rb')
    root = lxml.etree.parse(xmlFile).getroot()
    doc = document.Document(root)
    doc.filename = xmlInputName

    outputFile = None

    # If an output filename is specified, create an output filepointer for it
    if outputFileName is not None:
        if hasattr(outputFileName, 'write'):
            # it is already a file-like object
            outputFile = outputFileName
            outputFileName = 'output.odt'
        else:
            if outDir is not None:
                outputFileName = os.path.join(outDir, outputFileName)
            outputFile = open(outputFileName, 'wb')

    # Create a Reportlab canvas by processing the document
    doc.process(outputFile)

    if outputFile:
        outputFile.close()
    xmlFile.close()


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(
            prog='rml2pdf',
            description='Converts file in RML format into ODT file.',
            epilog='Copyright (c) 2017 Shoobx, Inc.'
        )
        parser.add_argument(
            'xmlInputName',
            help='RML file to be processed')
        parser.add_argument(
            'outputFileName', nargs='?',
            help='output ODT file name')
        parser.add_argument(
            'outDir', nargs='?',
            help='output directory')
        pargs = parser.parse_args()
        args = (
            pargs.xmlInputName, pargs.outputFileName,
            pargs.outDir,)

    go(*args)
