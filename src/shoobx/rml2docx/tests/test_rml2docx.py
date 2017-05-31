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
"""RML to DOCX Converter Tests
"""
from __future__ import absolute_import

import os
import subprocess
import unittest
from PIL import Image
from zope.interface import verify

from shoobx.rml2docx import interfaces, rml2docx

INPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2docx_data', 'input')
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2docx_data', 'output')
EXPECT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2docx_data', 'expected')

LOG_FILE = os.path.join(os.path.dirname(__file__), 'render.log')


def gs_command(path):
    return ('gs', '-q', '-sNOPAUSE', '-sDEVICE=png256',
            '-sOutputFile=%s[Page-%%d].png' % path[:-4],
            path, '-c', 'quit')

def unoconv_command(path, opath=None):
    if opath is None:
        opath = path.rsplit('.', 1)[0] + '.pdf'
    # XXX: For now, hardcode Pyhton 3 system directory. This is
    # needed, since unoconv is only installed for that version of python.
    return (
        '/usr/bin/python3', '/usr/bin/unoconv', '-vvv', '-f', 'pdf', '-o', opath, path)


class Rml2DocxConverterTest(unittest.TestCase):

    def test_interface(self):
        verify.verifyObject(interfaces.IRML2DOCX, rml2docx)


class Rml2DocxConverterFileTest(unittest.TestCase):

    def __init__(self, inputPath, outputPath):
        self.inputPath = inputPath
        self.outputPath = outputPath
        super(Rml2DocxConverterFileTest, self).__init__()

    def runTest(self):
        rml2docx.go(self.inputPath, self.outputPath)


class CompareDOCXTestCase(unittest.TestCase):

    level = 2

    def __init__(self, basePath, testPath):
        self._basePath = basePath
        self._testPath = testPath
        unittest.TestCase.__init__(self)

    def assertSameImage(self, baseImage, testImage):
        base_file = open(baseImage, 'rb')
        test_file = open(testImage, 'rb')
        base = Image.open(base_file).getdata()
        test = Image.open(test_file).getdata()
        for i in range(len(base)):
            if (base[i] - test[i]) != 0:
                self.fail(
                    'Image is not the same: %s' % os.path.basename(baseImage)
                )
        base_file.close()
        test_file.close()

    def runTest(self):
        # If the base DOCX file does not exist, throw an error.
        if not os.path.exists(self._basePath):
            raise RuntimeError(
                'The expected DOCX file is missing: ' + self._basePath)

        # If the base DOCX has not been converted to PDF yet, then
        # let's do that now.
        basePdfPath = self._basePath.rsplit('.', 1)[0] + '.pdf'
        if not os.path.exists(basePdfPath):
            status = subprocess.Popen(
                unoconv_command(self._basePath, basePdfPath)).wait()
            if status:
                raise ValueError(
                    'Base DOCX -> PDF conversion failed: %i' % status)

        # Convert the test DOCX file to PDF.
        testPdfPath = self._testPath.rsplit('.', 1)[0] + '.pdf'
        status = subprocess.Popen(
            unoconv_command(self._testPath, testPdfPath)).wait()
        if status:
            raise ValueError(
                'Test DOCX -> PDF conversion failed: %i' % status)

        # Convert the PDF file to image(s)
        status = subprocess.Popen(gs_command(basePdfPath)).wait()
        if status:
            raise ValueError(
                'Base PDF -> PNG conversion failed: %i' % status)

        # Convert the test PDF to image(s)
        status = subprocess.Popen(gs_command(testPdfPath)).wait()
        if status:
            raise ValueError(
                'Test PDF -> PNG conversion failed: %i' % status)

        # Go through all pages and ensure their equality
        n = 1
        while True:
            baseImage = self._basePath[:-4] + '[Page-%i].png' %n
            testImage = self._testPath[:-4] + '[Page-%i].png' %n
            if os.path.exists(baseImage) and os.path.exists(testImage):
                self.assertSameImage(baseImage, testImage)
            else:
                break
            n += 1


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(Rml2DocxConverterTest),
    ))

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    for inputFilename in os.listdir(INPUT_DIR):
        if not inputFilename.endswith('.rml'):
            continue

        inputPath = os.path.join(INPUT_DIR, inputFilename)
        outputPath = os.path.join(OUTPUT_DIR, inputFilename[:-3] + 'docx')
        expectPath = os.path.join(EXPECT_DIR, inputFilename[:-3] + 'docx')

        # ** Test RML to DOCX rednering! **
        testName = 'rml2docx-' + inputFilename[:-4]
        TestCase = type(testName, (Rml2DocxConverterFileTest,), {})
        case = TestCase(inputPath, outputPath)
        suite.addTest(case)

        # ** Test DOCX rendering correctness **
        testName = 'compare-'+inputFilename[:-4]
        TestCase = type(testName, (CompareDOCXTestCase,), {})
        case = TestCase(expectPath, outputPath)
        suite.addTest(case)

    return suite
