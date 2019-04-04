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

import unittest

from shoobx.rml2odt import document
from shoobx.rml2odt import flowable


class ParagraphTests(unittest.TestCase):

    def test_addSpaceHolders(self):
        doc = document.Document(None)
        element = ElementMock()
        para = flowable.Paragraph(element, doc)
        out = para._addSpaceHolders('text')
        out = self._processOut(out)
        self.assertEqual(out, 'text')

        out = para._addSpaceHolders('two words.')
        out = self._processOut(out)
        self.assertEqual(out, 'two words.')

        out = para._addSpaceHolders('Preformatted ')
        out = self._processOut(out)
        self.assertEqual(out, 'Preformatted ')

        out = para._addSpaceHolders(' only.  ')
        out = self._processOut(out)
        self.assertEqual(out, ' only.  ')

        out = para._addSpaceHolders('   only.  ')
        out = self._processOut(out)
        self.assertEqual(out, '   only.  ')

        out = para._addSpaceHolders('   two words.  ')
        out = self._processOut(out)
        self.assertEqual(out, '   two words.  ')

        out = para._addSpaceHolders('two  words.  ')
        out = self._processOut(out)
        self.assertEqual(out, 'two  words.  ')

    def _processOut(self, out):
        val = []
        for c in out.childNodes:
            if c.tagName == 'text:s':
                val.append(int(list(c.attributes.values())[0])*' ')
            else:
                val.append(str(c))
        return ''.join(val)



class ElementMock(dict):
    pass


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(ParagraphTests),
    ))

    return suite
