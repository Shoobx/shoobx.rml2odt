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
import six
import zope.interface

from z3c.rml import attr, directive
from z3c.rml import flowable as rml_flowable

from shoobx.rml2odt import flowable, stylesheet, list as lists
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
        if (self.element.text is None or not self.element.text.strip() or
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
            style = manager.document.getStyleByName(
                six.text_type(tableStyleName))
            return style
        except AssertionError:
            return None

    def processStyle(self):
        rows = len(self.parent.parent.element)
        cols = len(self.parent.parent.element[0])
        allowedCellProperties = ['backbackgroundcolor', 'paddingtop',
                                 'paddingbottom', 'paddingleft',
                                 'paddingright', 'padding',
                                 'textbackgroundcolor', 'verticalalign']
        allowedTableProperties = ['align']
        allowedColProperties = ['blockColBackground']
        allowedRowProperties = ['backgroundcolors']
        allowedTextProperties = ['fontname', 'fontsize']
        allowedParaProperties = ['leading']

        # Again we just want the style name or None, not the actual style
        tableStyleName = self.parent.parent.element.attrib.get('style')
        if tableStyleName is not None:
            stylesCollection = dict()
            desiredStyle = self.searchStyle(tableStyleName)
            if desiredStyle is not None:
                for child in desiredStyle.childNodes:
                    childAttrs = child.attributes
                    attrDict = {x[1]: childAttrs[x] for x in childAttrs}
                    for key in attrDict:
                        # 'backgroundcolor' is processed by cellProps
                        # 'backgroundcolor' passed in by 'rowProperties' is
                        # modified to 'backgroundcolors' for later distinction
                        if child.tagName == u'style:table-row-properties':
                            stylesCollection[str(key)+'s'] = str(attrDict[key])

                        elif key == u'background-color':
                            tmpval = str(attrDict[key])
                            identifier = tmpval[13:17]
                            stylesCollection[identifier+str(key)] = tmpval[2:9]

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
                    if key == 'backgroundcolors':
                        # Alternating rows
                        color1, color2 = value[2:9], value[13:20]
                        regex = '[0-9]+'
                        cellNo = int(re.findall(regex, self.cellStyleName)[0])

                        # Checks if this applies to alternating row colors
                        if 'row' in value:
                            if ((cellNo-1) // cols) % 2 == 0:
                                self.cellProps.setAttribute(key[:-1], color1)
                            else:
                                self.cellProps.setAttribute(key[:-1], color2)

                        # Checks if this applies to alternating columns
                        elif 'col' in value:
                            if ((cellNo - 1) % cols) % 2 == 0:
                                self.cellProps.setAttribute(key[:-1], color1)
                            else:
                                self.cellProps.setAttribute(key[:-1], color2)

        self.cellStyle.addElement(self.cellProps)
        self.contentStyle.addElement(self.textProps)
        self.contentStyle.addElement(self.paraProps)

    def process(self):
        manager = attr.getManager(self)

        col = len(self.parent.row.childNodes)
        row = len([x for x in self.parent.parent.table.childNodes
                  if x.tagName == u'table:table-row']) - 1

        # Cell creation and styling
        self.cellProps = odf.style.TableCellProperties()
        self.cellProps.setAttribute('shrinktofit', True)
        self.cellStyleName = manager.getNextStyleName('TableCell')
        self.cellStyle = odf.style.Style(
            name=self.cellStyleName,
            family='table-cell')

        kw = {}
        table_style = self.parent.parent.getAttributeValues(select=['style'])
        if table_style:
            table_style = table_style[0][1]

            for blockspan in [x for x in table_style.element.getchildren()
                              if x.tag == 'blockSpan']:
                attribs = blockspan.attrib
                start_col, start_row = map(int, attribs['start'].split(','))
                end_col, end_row = map(int, attribs['stop'].split(','))
                if end_col == -1:
                    end_col = self.parent.parent.columns()
                if end_row == -1:
                    end_row = self.parent.parent.rows()

                if (col >= start_col and col <= end_col and
                    row >= start_row and row <= end_row):
                    # This cell should span many cells
                    kw = {'numbercolumnsspanned': end_col - col,
                          'numberrowsspanned': end_row - row,}
                    break

        self.cell = odf.table.TableCell(
            stylename=self.cellStyleName,
            valuetype='string', **kw)

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
        attribs = dict(self.parent.getAttributeValues(
            attrMapping=self.parent.attrMapping))

        rowProps = odf.style.TableRowProperties()
        if 'rowHeights' in attribs:
            rowHeights = attribs['rowHeights']
            rowHeight = rowHeights[TableRow.count]
            rowProps.setAttribute('rowheight', '%spt' % rowHeight)
            # XXX is this needed? /lennart
            self.element.attrib['rowHeight'] = '%spt' % rowHeight
        else:
            rowProps.setAttribute('useoptimalrowheight', True)

        manager = attr.getManager(self)
        self.styleName = manager.getNextStyleName('TableRow')
        style = odf.style.Style(name=self.styleName, family='table-row')
        manager.document.automaticstyles.addElement(style)
        style.addElement(rowProps)
        TableRow.count += 1

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
        cols = max(len(e) for e in self.element)
        rows = len(self.element)
        # Creates the colWidths and rowHeights if they do not already exist
        attribs = dict(self.getAttributeValues())
        if 'rowHeights' in attribs:
            tempHeights = attribs['rowHeights']

        colWidths = attribs.get('colWidths', [])

        manager = attr.getManager(self)
        for idx in range(cols):
            # Create a style for each col.
            styleName = manager.getNextStyleName('TableColumn')
            style = odf.style.Style(name=styleName, family='table-column')
            manager.document.automaticstyles.addElement(style)
            colProps = odf.style.TableColumnProperties()
            style.addElement(colProps)
            # Apply the width if available.
            if colWidths:
                colWidth = colWidths[idx]
                if (isinstance(colWidth, six.string_types) and
                   colWidth.endswith('%')):
                    colProps.setAttribute('relcolumnwidth',
                                          colWidth[:-1] + '*')
                else:
                    colProps.setAttribute('columnwidth', colWidth)

            self.table.addElement(odf.table.TableColumn(stylename=styleName))

    def convertBulkData(self):
        # Checks if bulktable in tag and dynamically adds colWidths and
        # rowHeights to the parent (blockTable)
        element = self.element.getchildren()[0]
        return element.tag == 'bulkData'

    def process(self):
        TableRow.count = 0
        # Naive way of determining the size of the table.
        rows = len(self.element)
        manager = attr.getManager(self)
        if not rows:
            raise ValueError('Empty table')

        try:
            styleName = self.element.attrib.get('style')
        except KeyError:
            styleName = manager.getNextStyleName('Table')
            style = odf.style.Style(name=styleName, family='table')
            manager.document.automaticstyles.addElement(style)
            tableProps = odf.style.TableProperties(relwidth='100%')
            style.addElement(tableProps)

        self.table = odf.table.Table(stylename=styleName)
        if isinstance(self.parent, TableCell):
            self.table.setAttribute('issubtable', 'true')

        if isinstance(self.parent, lists.ListItem):
            # ODT doesn't allow tables in list-items, so we add it to
            # office:text. This means it will lack indentation, but I don't
            # know how to get the indentation of the list-item, it's likely
            # not calculated at this point anyway.
            ob = self.parent.parent
            while ob is not None:
                if (getattr(getattr(ob, 'contents'), 'tagName') ==
                   u'office:text'):
                    break
                ob = ob.parent
            ob.contents.addElement(self.table)
        else:
            self.contents.addElement(self.table)

        flag = self.convertBulkData()
        if not flag:
            self.addColumns()
        self.processSubDirectives()

    def rows(self):
        return len([e for e in self.element.getchildren()
                    if e.tag == 'tr'])

    def columns(self):
        return max([len([e for e in row.getchildren() if e.tag == 'td'])
                     for row in self.element.getchildren()])


flowable.Flow.factories['blockTable'] = BlockTable
