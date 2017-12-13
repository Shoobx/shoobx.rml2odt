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
import re
import subprocess
import sys
import unittest
import zipfile
from PIL import Image
from zope.interface import verify
from odf.element import Element

from shoobx.rml2odt import interfaces, rml2odt

INPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_data', 'input')
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_data', 'output')
EXPECT_DIR = os.path.join(
    os.path.dirname(__file__), 'test_data', 'expected')

LOG_FILE = os.path.join(os.path.dirname(__file__), 'render.log')

UNOCONV_BIN = os.path.join(
    os.path.dirname(sys.executable), 'unoconv')
PYTHON_OFFICE_BIN = os.environ.get('PYTHON_OFFICE_BIN')

ENV_PATH = os.path.abspath('env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as env_file:
        PYTHON_OFFICE_BIN = env_file.read().strip()

NORMALIZE_CONTENT_RES = [re.compile(attrib+'\=\".*?\"')
                         for attrib in ('xml:id', 'text:continue-list')]


def gs_command(path):
    cmd = (
        'gs', '-q', '-sDEVICE=png256',
        '-o', '%s[Page-%%d].png' % path[:-3],
        path)
    return cmd


def unoconv_command(path, opath=None):
    if opath is None:
        opath = path[:-4] + '.pdf'
    cmd = (
        PYTHON_OFFICE_BIN, UNOCONV_BIN, '-vvv', '-T', '15', '-f',
        'pdf', '-o', opath, path)
    return cmd


class Rml2OdtConverterTest(unittest.TestCase):

    def test_interface(self):
        verify.verifyObject(interfaces.IRML2ODT, rml2odt)

    def test_convertString(self):
        instr = """<?xml version="1.0" encoding="iso-8859-1" standalone="no"?>
<!DOCTYPE document SYSTEM "rml.dtd">

<document filename="hello-world.pdf">

  <template>
    <pageTemplate id="main">
      <frame id="first" x1="1cm" y1="1cm" width="19cm" height="26cm"/>
    </pageTemplate>
  </template>

  <story>
    <para>Hello <i>World</i>!</para>
  </story>

</document>"""
        result = rml2odt.convertString(instr)
        # The resulting output is indeed a zip file, so the conversion
        # succeeded.
        self.assertEqual(result.getvalue()[:2], b'PK')



class Rml2OdtConverterFileTest(unittest.TestCase):

    def __init__(self, inputPath, outputPath, expectPath):
        self.inputPath = inputPath
        self.outputPath = outputPath
        self.expectPath = expectPath
        super(Rml2OdtConverterFileTest, self).__init__()

    def runTest(self):
        rml2odt.convertFile(self.inputPath, self.outputPath)
        expected = zipfile.ZipFile(self.expectPath, 'r')
        output = zipfile.ZipFile(self.outputPath, 'r')
        expected_names = set(expected.namelist())
        output_names = set(output.namelist())

        if expected_names != output_names:
            raise ValueError("ODT namelist doesn't match expectations for "
                             "RML file %s.\nIs %s, should be %s." % (
                                 self.inputPath, output_names, expected_names))

    def _normalize(self, text):
        for regexp in NORMALIZE_CONTENT_RES:
            text = regexp.sub('', text)
        return text


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
        if not os.path.exists(basePdfPath):
            command = unoconv_command(self._basePath)
            status = subprocess.Popen(command).wait()
            if status:
                raise ValueError(
                    'Base ODT -> PDF conversion failed: %i\n'
                    'Command line %s' % (status, ' '.join(command)))

        # If the base PDF isn't converted into images, do that now:
        basePNGPath = self._basePath.rsplit('.', 1)[0] + '.[Page-1].png'
        # We only check the first image, because we don't know how
        # many pages there are.
        if not os.path.exists(basePNGPath):
            status = subprocess.Popen(gs_command(basePdfPath)).wait()
            if status:
                raise ValueError(
                    'Base PDF -> PNG conversion failed: %i' % status)

        # Convert the test ODT file to PDF.
        testPdfPath = self._testPath.rsplit('.', 1)[0] + '.pdf'
        status = subprocess.Popen(
            unoconv_command(self._testPath)).wait()

        if status:
            raise ValueError(
                'Test ODT -> PDF conversion failed: %i' % status)

        # Convert the test PDF to image(s)
        status = subprocess.Popen(gs_command(testPdfPath)).wait()
        if status:
            raise ValueError(
                'Test PDF -> PNG conversion failed: %i' % status)

        # Go through all images and ensure their equality
        n = 1
        while True:
            baseImage = self._basePath[:-4] + '.[Page-%i].png' % n
            testImage = self._testPath[:-4] + '.[Page-%i].png' % n
            if os.path.exists(baseImage):
                if not os.path.exists(testImage):
                    raise RuntimeError(
                        'The expected PNG file is missing: %s' % testImage)

                self.assertSameImage(baseImage, testImage)
            else:
                if os.path.exists(testImage):
                    raise AssertionError('Unexpected PNG file: %s' % testImage)
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
        testName = 'rml2odt-' + inputFilename[:-4]
        TestCase = type(testName, (Rml2OdtConverterFileTest,), {})
        case = TestCase(inputPath, outputPath, expectPath)
        suite.addTest(case)

        # ** Test ODT rendering correctness **
        testName = 'compare-'+inputFilename[:-4]
        TestCase = type(testName, (CompareODTTestCase,), {})
        case = TestCase(expectPath, outputPath)
        suite.addTest(case)

    return suite
