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
import odf.table
from z3c.rml import attr, directive
from z3c.rml import flowable as rml_flowable
import zope.interface

from shoobx.rml2odt import flowable
from shoobx.rml2odt.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class TableCell(flowable.Flow):
    signature = rml_flowable.ITableCell
    styleAttributesMapping = rml_flowable.TableCell.styleAttributesMapping

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
        self.cell = odf.table.TableCell(valuetype='string')
        self.parent.row.addElement(self.cell)
        self.contents = self.cell
        super(TableCell, self).process()


class TableBulkData(directive.RMLDirective):
	signature = rml_flowable.ITableBulkData

	def process(self):
		contents = self.element.text.strip().split('\n')
		contents = [x.strip() for x in contents]
		# newTable = lxml.etree.Element('blockTable')
		for rowData in contents:
			newRow = lxml.etree.Element('tr')
			for cell in range(len(rowData.split(','))):
				newCell = lxml.etree.Element('td')
				newCell.text = rowData.split(',')[cell]
				newRow.append(newCell)
			self.parent.element.append(newRow)
		
		self.parent.element.remove(self.element)
		self.parent.process()
		#self.element.append(newTable)
			

class TableRow(directive.RMLDirective):
    signature = rml_flowable.ITableRow
    factories = {'td': TableCell}
    count = 0

    def styleRow(self):
    	rowHeights = self.parent.getAttributeValues(
            select=['rowHeights'], valuesOnly=True)[0]
    	# XXX: Finish this to use for conversion of rowHeights
    	# rh = self.parent.element.attrib['rowHeights'].split(" ")
    	rowHeight = rowHeights[TableRow.count]
    	manager = attr.getManager(self)
    	self.styleName = manager.getNextSyleName('TableRow')
    	style = odf.style.Style(name=self.styleName, family='table-row')
    	manager.document.automaticstyles.addElement(style)
    	rowProps = odf.style.TableRowProperties()
    	style.addElement(rowProps)
    	rowProps.setAttribute('rowheight', rowHeight)
    	TableRow.count+=1


    def process(self):
    	self.styleRow()
        self.row = odf.table.TableRow(stylename=self.styleName)
        self.parent.table.addElement(self.row)
        self.processSubDirectives()


class BlockTable(flowable.Flowable):
    signature = rml_flowable.IBlockTable
    factories = {
        'tr': TableRow,
        'bulkData': TableBulkData,
        # 'blockTableStyle': BlockTableStyle
    }

    def addColumns(self):
        cols = len(self.element[0])
        colWidths = self.getAttributeValues(
            select=['colWidths'], valuesOnly=True)[0]
        if colWidths and len(colWidths) != len(self.element[0]):
        	raise ValueError('colWidths` entries do not match column count.')

        manager = attr.getManager(self)
        for idx in range(cols):
            # Create a style for each col.
            styleName = manager.getNextSyleName('TableColumn')
            style = odf.style.Style(name=styleName, family='table-column')
            manager.document.automaticstyles.addElement(style)
            colProps = odf.style.TableColumnProperties()
            style.addElement(colProps)
            # Apply the width if available.
            colWidth = colWidths[idx]
            if colWidth.endswith('%'):
                colProps.setAttribute('relcolumnwidth', colWidth[:-1] + '*')
            else:
                colProps.setAttribute('columnwidth', colWidth)
            self.table.addElement(odf.table.TableColumn(stylename=styleName))


    def preliminaryBulkTables(self):
        element = self.element.getchildren()[0]
        if element.tag != 'bulkData':
            self.addColumns()
    	else:
    		contents = element.text
    		numOfCols = contents.strip().split('\n')
    		rowHeights = "10cm "*len(numOfCols)
    		numOfCols = max([len(x.split(',')) for x in numOfCols])
    		base_width = 100/numOfCols
    		colWidths = [str(base_width)+'%' for x in range(numOfCols)]
    		colWidths = " ".join(colWidths)
    		self.element.attrib['colWidths'] = colWidths
    		self.element.attrib['rowHeights'] = rowHeights


    def process(self):
    	TableRow.count = 0
        # Naive way of determining the size of the table.
        rows = len(self.element)
        if not rows:
            raise ValueError('Empty table')
        manager = attr.getManager(self)
        styleName = manager.getNextSyleName('Table')
        style = odf.style.Style(name=styleName, family='table')
        manager.document.automaticstyles.addElement(style)
        tableProps = odf.style.TableProperties(relwidth='100%')
        style.addElement(tableProps)
        self.table = odf.table.Table(stylename=styleName)
        self.contents.addElement(self.table)
    	self.preliminaryBulkTables()
        self.processSubDirectives()


flowable.Flow.factories['blockTable'] = BlockTable
