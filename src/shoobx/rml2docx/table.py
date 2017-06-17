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
"""``blockTableStyle``, ``blockTable``, ``row``, ``tr``, and ``td`` directives.
"""
import lxml.etree
from z3c.rml import directive
from z3c.rml import flowable as rml_flowable
import zope.interface

from shoobx.rml2docx import flowable
from shoobx.rml2docx.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class TableCell(flowable.Flow):
    signature = rml_flowable.ITableCell
    styleAttributesMapping = rml_flowable.TableCell.styleAttributesMapping

    @property
    def table(self):
        return self.parent.parent.table

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.
        # 1. Is there text in the element?
        # 2. Are any of the children valid Flow elements?
        if (not self.element.text.strip() or
            any([sub.tag in flowable.Flow.factories
                 for sub in self.element])):
            return
        # Create a <para> element.
        para = lxml.etree.Element('para')
        # Transfer text.
        para.text = self.element.text
        self.element.text = None
        # Transfer children.
        for sub in tuple(self.element):
            para.append(sub)
        # Add paragraph to table cell.
        self.element.append(para)

    def process(self):
        self._convertSimpleContent()
        self.container = self.parent.row.cells[self.parent.colIdx]
        self.width = self.table.columns[self.parent.colIdx].width
        # Remove the empty paragraph that got added automatically.
        p = self.container.paragraphs[0]._element
        p.getparent().remove(p)
        p._p = p._element = None
        super(TableCell, self).process()
        self.parent.colIdx += 1


class TableRow(directive.RMLDirective):
    signature = rml_flowable.ITableRow
    factories = {'td': TableCell}

    @property
    def table(self):
        return self.parent.table

    def process(self):
        self.row = self.table.rows[self.parent.rowIdx]
        self.colIdx = 0
        self.processSubDirectives()
        self.parent.rowIdx += 1


class BlockTable(flowable.Flowable):
    signature = rml_flowable.IBlockTable
    factories = {
        'tr': TableRow,
        # 'bulkData': TableBulkData,
        # 'blockTableStyle': BlockTableStyle
    }

    def applyDimensions(self):
        colWidths = self.getAttributeValues(
            select=['colWidths'], valuesOnly=True)[0]
        if len(colWidths) != len(self.element[0]):
            raise ValueError('colWidths` entries do not match column count.')
        self.table.allow_autofit = False

        # Get container width.
        cc = self.parent
        while not IContentContainer.providedBy(cc):
            cc = cc.parent
        availWidth = cc.width

        for colWidth, col in zip(colWidths, self.table.columns):
            if colWidth.endswith('%'):
                colWidth = availWidth*int(colWidth[:-1])/100
            col.width = colWidth

    def process(self):
        # Naive way of determining the size of the table.
        rows = len(self.element)
        if not rows:
            raise ValueError('Empty table')
        cols = len(self.element[0])
        self.table = self.parent.container.add_table(rows, cols)
        self.applyDimensions()
        self.rowIdx = 0
        self.processSubDirectives()


flowable.Flow.factories['blockTable'] = BlockTable
