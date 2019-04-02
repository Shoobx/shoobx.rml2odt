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

import lxml
import unittest

from shoobx.rml2odt import document
from shoobx.rml2odt import table
from shoobx.rml2odt import stylesheet

STYLE1 = """
    <blockTableStyle id="table">
        <blockAlignment value="center"/>
        <blockValign value="middle" start="-1,0" stop="-1,-1"/>
        <blockSpan start="0,0" stop="2,0"/>
        <blockSpan start="-2,0" stop="-1,-1"/>
        <blockSpan start="3,3" stop="6,6"/>
        <lineStyle kind="GRID" colorName="black" start="0,1" stop="-2,-1"/>
        <lineStyle kind="GRID" colorName="black" start="3,0" stop="3,0"/>
        <lineStyle kind="OUTLINE" colorName="black" thickness="2"/>
    </blockTableStyle>
"""

EXPECTED1 = """
|(3, 1)|      |      | cell | cell | cell | cell | cell |(2, 9)|      |
| cell | cell | cell | cell | cell | cell | cell | cell |      |      |
| cell | cell | cell | cell | cell | cell | cell | cell |      |      |
| cell | cell | cell |(4, 4)|      |      |      | cell |      |      |
| cell | cell | cell |      |      |      |      | cell |      |      |
| cell | cell | cell |      |      |      |      | cell |      |      |
| cell | cell | cell |      |      |      |      | cell |      |      |
| cell | cell | cell | cell | cell | cell | cell | cell |      |      |
| cell | cell | cell | cell | cell | cell | cell | cell |      |      |
"""

STYLE2 = """
    <blockTableStyle id="table">
      <lineStyle start="0,0" stop="-1,-1" kind="GRID"
                 thickness="0.5" colorName="grey" />
      <blockBackground start="0,0" stop="1,1" colorName="palegreen" />
      <blockSpan start="0,0" stop="1,1" />
      <blockBackground start="-2,-2" stop="-1,-1" colorName="pink" />
      <blockSpan start="-2,-2" stop="-1,-1" />
    </blockTableStyle>
"""


EXPECTED2 = """
|(2, 2)|      | cell | cell | cell |
|      |      | cell | cell | cell |
| cell | cell | cell |(2, 2)|      |
| cell | cell | cell |      |      |
"""

STYLE3 = """
    <blockTableStyle id="table">
      <lineStyle start="0,0" stop="-1,-1" kind="GRID"
                 thickness="0.5" colorName="grey" />
      <blockBackground start="0,0" stop="1,1" colorName="palegreen" />
      <blockSpan start="0,0" stop="1,0" />
      <blockBackground start="-2,-2" stop="-1,-1" colorName="pink" />
      <blockSpan start="2,1" stop="2,2" />
      <blockSpan start="-1,-2" stop="-1,-1" />
      <blockSpan start="0,3" stop="0,3" />
    </blockTableStyle>
"""

EXPECTED3 = """
|(2, 1)|      | cell | cell | cell |
| cell | cell |(1, 2)| cell | cell |
| cell | cell |      | cell |(1, 2)|
| cell | cell | cell | cell |      |
"""

class BlockTableTests(unittest.TestCase):

    def test_spanmap_1(self):
        tbl = self._getTable(STYLE1)
        tbl.rows = 9
        tbl.columns = 10
        res = tbl.spanmap

        out = self._processResult(res, 10, 9)

        self.assertEqual(out, EXPECTED1.strip())

    def test_spanmap_2(self):
        tbl = self._getTable(STYLE2)
        tbl.rows = 4
        tbl.columns = 5
        res = tbl.spanmap

        out = self._processResult(res, 5, 4)

        self.assertEqual(out, EXPECTED2.strip())

    def test_spanmap_3(self):
        tbl = self._getTable(STYLE3)
        tbl.rows = 4
        tbl.columns = 5
        res = tbl.spanmap

        out = self._processResult(res, 5, 4)

        self.assertEqual(out, EXPECTED3.strip())

    def _getTable(self, style):
        btsroot = lxml.etree.fromstring(style)
        bts = stylesheet.BlockTableStyle(btsroot, None)
        doc = document.Document(None)
        doc.styles['table'] = bts
        element = ElementMock(style='table')
        element.sourceline = 123
        tbl = table.BlockTable(element, doc)
        return tbl
    
    def _processResult(self, res, cols, rows):
        out = ''
        for row in range(rows):
            out += '|'
            for col in range(cols):
                val = res[col][row]
                if val:
                    if isinstance(val, dict):
                        val = (val.get('numbercolumnsspanned', 1),
                               val.get('numberrowsspanned', 1))
                        out += str(val) #  '(1, 0)'
                    else:
                        out += ' cell '
                elif val is False:
                    out += '      '
                else:
                    out += ' ???? '
                out += '|'
            out += '\n'
        
        if False:
            print
            print(out)
            
        return out.strip()


class Mock(object):
    pass


class ElementMock(dict):
    pass


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(BlockTableTests),
    ))

    return suite
