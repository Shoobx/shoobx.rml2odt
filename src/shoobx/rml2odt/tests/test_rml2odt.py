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
import sys
import unittest
from PIL import Image
from zope.interface import verify

from shoobx.rml2odt import interfaces, rml2odt

INPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2odt_data', 'input')
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2odt_data', 'output')
EXPECT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_rml2odt_data', 'expected')

LOG_FILE = os.path.join(os.path.dirname(__file__), 'render.log')

UNOCONV_BIN = os.path.join(
    os.path.dirname(sys.executable), 'unoconv')
PYTHON_OFFICE_BIN = os.environ.get('PYTHON_OFFICE_BIN')

ENV_PATH = os.path.abspath('env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as env_file:
        PYTHON_OFFICE_BIN=env_file.read().strip()


def gs_command(path):
    cmd = (
        'gs', '-q', '-sDEVICE=png256',
        '-o', '%s[Page-%%d].png' % path[:-3],
        path)
    return cmd


def unoconv_command(path, opath=None):
    if opath is None:
        opath = path[:-5] + '.pdf'
    cmd = (
        PYTHON_OFFICE_BIN, UNOCONV_BIN, '-vvv', '-T', '15', '-f',
        'pdf', '-o', opath, path)
    return cmd


class Rml2OdtConverterTest(unittest.TestCase):

    def test_interface(self):
        verify.verifyObject(interfaces.IRML2ODT, rml2odt)


class Rml2OdtConverterFileTest(unittest.TestCase):

    def __init__(self, inputPath, outputPath):
        self.inputPath = inputPath
        self.outputPath = outputPath
        super(Rml2OdtConverterFileTest, self).__init__()

    def runTest(self):
        rml2odt.go(self.inputPath, self.outputPath)


class CompareODTTestCase(unittest.TestCase):

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
        # If the base ODT file does not exist, throw an error.
        if not os.path.exists(self._basePath):
            raise RuntimeError(
                'The expected ODT file is missing: ' + self._basePath)

        # If the base ODT has not been converted to PDF yet, then
        # let's do that now.
        basePdfPath = self._basePath.rsplit('.', 1)[0] + '.pdf'
        status = subprocess.Popen(
            unoconv_command(self._basePath)).wait()
        if status:
            raise ValueError(
                'Base ODT -> PDF conversion failed: %i' % status)

        # Convert the test ODT file to PDF.
        testPdfPath = self._testPath.rsplit('.', 1)[0] + '.pdf'
        status = subprocess.Popen(
            unoconv_command(self._testPath)).wait()

        if status:
            raise ValueError(
                'Test ODT -> PDF conversion failed: %i' % status)

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
            baseImage = self._basePath[:-5] + '[Page-%i].png' %n
            testImage = self._testPath[:-5] + '[Page-%i].png' %n
            if os.path.exists(baseImage) and os.path.exists(testImage):
                self.assertSameImage(baseImage, testImage)
            else:
                break
            n += 1


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(Rml2OdtConverterTest),
    ))

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    for inputFilename in os.listdir(INPUT_DIR):
        if not inputFilename.endswith('.rml'):
            continue

        inputPath = os.path.join(INPUT_DIR, inputFilename)
        outputPath = os.path.join(OUTPUT_DIR, inputFilename[:-3] + 'odt')
        expectPath = os.path.join(EXPECT_DIR, inputFilename[:-3] + 'odt')

        # ** Test RML to ODT rednering! **
        testName = 'rml2odt-' + inputFilename[:-3]
        TestCase = type(testName, (Rml2OdtConverterFileTest,), {})
        case = TestCase(inputPath, outputPath)
        suite.addTest(case)

        # ** Test ODT rendering correctness **
        testName = 'compare-'+inputFilename[:-3]
        TestCase = type(testName, (CompareODTTestCase,), {})
        case = TestCase(expectPath, outputPath)
        suite.addTest(case)

    return suite
