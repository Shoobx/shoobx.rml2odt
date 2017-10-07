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
import re
import zope.interface

from z3c.rml import attr, directive
from z3c.rml import flowable as rml_flowable

from shoobx.rml2odt import flowable, stylesheet
from shoobx.rml2odt.interfaces import IContentContainer

DEFAULT_TABLE_UNIT = 'mm'

@zope.interface.implementer(IContentContainer)
class TableCell(flowable.Flow):
    signature = rml_flowable.ITableCell
    styleAttributesMapping = rml_flowable.TableCell.styleAttributesMapping

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.
        # 1. Is there text in the element?
        # 2. Are any of the children valid Flow elements?
        if (self.element.text == None or not self.element.text.strip() or
            any([sub.tag in flowable.Flow.factories
                 for sub in self.element])):
            return

        # Create a <para> element.
        para = lxml.etree.Element('para', style=self.cellContentStyleName)

        # Transfer text.
        para.text = self.element.text
        self.element.text = None

        # Transfer children.
        for sub in tuple(self.element):
            para.append(sub)

        # Add paragraph to table cell.
        self.element.append(para)

    def searchStyle(self, tableStyleName):
        manager = attr.getManager(self)
        try:
            style = manager.document.getStyleByName(unicode(tableStyleName))
            return style
        except:
            return None

    def processStyle(self):
        rows = len(self.parent.parent.element)
        cols = len(self.parent.parent.element[0])
        allowedCellProperties = ['backbackgroundcolor','paddingtop',
                                 'paddingbottom', 'paddingleft', 'paddingright', 'padding',
                                 'textbackgroundcolor', 'verticalalign']
        allowedTableProperties = ['align']
        allowedColProperties = ['blockColBackground']
        allowedRowProperties = ['backgroundcolors']
        allowedTextProperties = ['fontname', 'fontsize']
        allowedParaProperties = ['leading']

        tableStyleName = self.parent.parent.element.attrib.get('style', None)
        if tableStyleName != None:
            stylesCollection = dict()
            desiredStyle = self.searchStyle(tableStyleName)
            if desiredStyle != None:
                children = desiredStyle.childNodes

                for child in children:
                    childAttrs = child.attributes
                    attrDict = dict([(x[1], childAttrs[x]) for x in childAttrs])
                    for key in attrDict:
                        # 'backgroundcolor' is processed by cellProps
                        # 'backgroundcolor' passed in by 'rowProperties' is
                        # modified to 'backgroundcolors' for later distinction
                        if child.tagName == u'style:table-row-properties':
                            stylesCollection[str(key)+'s'] = str(attrDict[key])

                        elif key == u'background-color':
                            tempVal = str(attrDict[key])
                            identifier = tempVal[13:17]
                            stylesCollection[identifier+str(key)] = tempVal[2:9]

                        else:
                            stylesCollection[str(key)] = str(attrDict[key])

            for key in stylesCollection:
                value = stylesCollection[key]
                key = key.replace('-', '')

                # Column Properties
                if key in allowedColProperties:
                    pass

                # Cell Properties
                elif key in allowedCellProperties:
                    if key == 'textbackgroundcolor':
                        self.textProps.setAttribute('color', value)
                    elif key == 'backbackgroundcolor':
                        self.cellProps.setAttribute('backgroundcolor', value)
                    else:
                        self.cellProps.setAttribute(key, value)

                # Table Properties
                elif key in allowedTableProperties:
                    if key == 'align':
                        self.paraProps.setAttribute('textalign', value)
                    else:
                        # XXX: come back to this
                        self.paraProps.setAttribute(key, value)

                # Paragraph Properties
                elif key in allowedParaProperties:
                    self.paraProps.setAttribute(key, value)

                # Text Properties
                elif key in allowedTextProperties:
                    self.textProps.setAttribute(key, value)

                # Row Properties
                elif key in allowedRowProperties:
                    if key=='backgroundcolors':
                        # Alternating rows
                        color1, color2 = value[2:9], value[13:20]
                        regex = '[0-9]+'
                        cellNo = int(re.findall(regex, self.cellStyleName)[0])

                        # Checks if this applies to alternating row colors
                        if 'row' in value:
                            if ((cellNo-1)//cols)%2 == 0:
                                self.cellProps.setAttribute(key[:-1], color1)
                            else:
                                self.cellProps.setAttribute(key[:-1], color2)

                        # Checks if this applies to alternating columns
                        elif 'col' in value:
                            if ((cellNo-1)%cols)%2 == 0:
                                self.cellProps.setAttribute(key[:-1], color1)
                            else:
                                self.cellProps.setAttribute(key[:-1], color2)

        self.cellStyle.addElement(self.cellProps)
        self.contentStyle.addElement(self.textProps)
        self.contentStyle.addElement(self.paraProps)

    def process(self):
        manager = attr.getManager(self)

        # Cell creation and styling
        self.cellProps  = odf.style.TableCellProperties()
        self.cellProps.setAttribute('shrinktofit', True)
        self.cellStyleName = manager.getNextStyleName('TableCell')
        self.cellStyle = odf.style.Style(
            name=self.cellStyleName,
            family='table-cell')
        self.cell = odf.table.TableCell(
            stylename=self.cellStyleName,
            valuetype='string')

        # Cell Text styling
        self.cellContentStyleName = manager.getNextStyleName('CellContent')
        self.contentStyle = odf.style.Style(
            name=self.cellContentStyleName,
            family='paragraph')

        # XXX: Has textalign, justifysingleword
        self.paraProps = odf.style.ParagraphProperties()
        # XXX: Has color (text color)
        self.textProps = odf.style.TextProperties()
        self.contentStyle.addElement(self.paraProps)

        self._convertSimpleContent()
        self.processStyle()
        self.parent.row.addElement(self.cell)
        self.contents = self.cell
        super(TableCell, self).process()

        manager.document.automaticstyles.addElement(self.cellStyle)
        manager.document.automaticstyles.addElement(self.contentStyle)


class TableBulkData(directive.RMLDirective):
    signature = rml_flowable.ITableBulkData

    def process(self):
        # Retrieves the text in the bulkData tag.
        contents = self.element.text.strip().split('\n')
        contents = [x.strip() for x in contents]
        # Converts the retrieved text into table row and cell objects
        for rowData in contents:
            newRow = lxml.etree.Element('tr')
            for cell in range(len(rowData.split(','))):
                newCell = lxml.etree.Element('td')
                newCell.text = rowData.split(',')[cell]
                newRow.append(newCell)
            self.parent.element.append(newRow)
        # Removes bulkData object so that recursion loop does not occur
        self.parent.element.remove(self.element)
        self.parent.process()


class TableRow(directive.RMLDirective):
    signature = rml_flowable.ITableRow
    factories = {'td': TableCell}
    count = 0

    def styleRow(self):
        rowHeights = self.parent.element.attrib['rowHeights'].split(' ')
        # XXX: Finish this to use for conversion of rowHeights
        # rh = self.parent.element.attrib['rowHeights'].split(" ")
        rowHeight = rowHeights[TableRow.count] + DEFAULT_TABLE_UNIT
        manager = attr.getManager(self)
        self.styleName = manager.getNextStyleName('TableRow')
        style = odf.style.Style(name=self.styleName, family='table-row')
        manager.document.automaticstyles.addElement(style)
        rowProps = odf.style.TableRowProperties()
        style.addElement(rowProps)
        rowProps.setAttribute('rowheight', rowHeight)
        # ??
        rowProps.setAttribute('useoptimalrowheight', True)
        self.element.attrib['rowHeight'] = unicode(rowHeight)
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
    }

    def addColumns(self):
        cols = len(self.element[0])
        rows = len(self.element)
        # Creates the colWidths and rowHeights if they do not already exist
        try:
            tempHeights = self.element.attrib['rowHeights'].split(',')
            if tempHeights[0].isdigit():
                temp = ' '.join([x + DEFAULT_TABLE_UNIT for x in tempHeights])
                self.element.attrib['rowHeights'] = temp
        except:
            self.element.attrib['rowHeights'] = "30%s "%DEFAULT_TABLE_UNIT * rows

        try:
            self.element.attrib['colWidths']
        except:
            base_width = str(100/cols) + '% '
            self.element.attrib['colWidths'] = base_width * cols


        colWidths = self.getAttributeValues(
            select=['colWidths'], valuesOnly=True)[0]

        if colWidths and len(colWidths) != len(self.element[0]):
            raise ValueError('colWidths` entries do not match column count.')

        manager = attr.getManager(self)
        for idx in range(cols):
            # Create a style for each col.
            styleName = manager.getNextStyleName('TableColumn')
            style = odf.style.Style(name=styleName, family='table-column')
            manager.document.automaticstyles.addElement(style)
            colProps = odf.style.TableColumnProperties()
            style.addElement(colProps)
            # Apply the width if available.
            colWidth = colWidths[idx]

            if isinstance(colWidth, basestring) and colWidth.endswith('%'):
                colProps.setAttribute('relcolumnwidth', colWidth[:-1] + '*')
            else:
                colProps.setAttribute('columnwidth', colWidth)
            self.table.addElement(odf.table.TableColumn(stylename=styleName))


    def convertBulkData(self):
        # Checks if bulktable in tag and dynamically adds colWidths and
        # rowHeights to the parent (blockTable)
        element = self.element.getchildren()[0]
        if element.tag != 'bulkData':
            return False
        else:
            contents = element.text
            numOfCols = contents.strip().split('\n')
            rowHeights = "30%s "%DEFAULT_TABLE_UNIT *len(numOfCols)

            # This may be a problem !!
            numOfCols = max([len(x.split(',')) for x in numOfCols])

            base_width = 100/numOfCols
            colWidths = [str(base_width)+'%' for x in range(numOfCols)]
            colWidths = " ".join(colWidths)
            self.element.attrib['colWidths'] = colWidths
            self.element.attrib['rowHeights'] = rowHeights
            return True


    def process(self):
        TableRow.count = 0
        # Naive way of determining the size of the table.
        rows = len(self.element)
        manager = attr.getManager(self)
        if not rows:
            raise ValueError('Empty table')

        try:
            styleName = self.element.attrib.get('style')
        except:
            styleName = manager.getNextStyleName('Table')
            style = odf.style.Style(name=styleName, family='table')
            manager.document.automaticstyles.addElement(style)
            tableProps = odf.style.TableProperties(relwidth='100%')
            style.addElement(tableProps)

        self.table = odf.table.Table(stylename=styleName)
        if isinstance(self.parent, TableCell):
            self.table.setAttribute('issubtable', 'true')
        self.contents.addElement(self.table)
        flag = self.convertBulkData()
        if not flag:
            self.addColumns()
        self.processSubDirectives()


flowable.Flow.factories['blockTable'] = BlockTable

