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
import lazy
import lxml.etree
import odf.table
import re
import six
import zope.interface

from z3c.rml import attr, directive
from z3c.rml import flowable as rml_flowable

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
        if (self.element.text is None or not self.element.text.strip() or
            any([sub.tag in self.factories for sub in self.element])):
            return

        # Create a <para> element.
        para = lxml.etree.Element('para', style=self.cellContentStyleName)

        # Transfer text.
        para.text = self.element.text
        # Nuke text instead of removing the current element
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
                    end_col = self.parent.parent.columns
                if end_row == -1:
                    end_row = self.parent.parent.rows

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


class TableRow(directive.RMLDirective):
    signature = rml_flowable.ITableRow
    factories = {'td': TableCell}

    def styleRow(self):
        attribs = dict(self.parent.getAttributeValues(
            attrMapping=self.parent.attrMapping))

        rowProps = odf.style.TableRowProperties()
        rowHeight = None
        if 'rowHeights' in attribs:
            rowHeights = attribs['rowHeights']
            try:
                rowHeight = rowHeights[self.parent.rowCount]
            except IndexError:
                # don't burp just in case RML specified less data
                pass
        if rowHeight is None:
            rowProps.setAttribute('useoptimalrowheight', True)
        else:
            rowProps.setAttribute('rowheight', '%spt' % rowHeight)

        manager = attr.getManager(self)
        self.styleName = manager.getNextStyleName('TableRow')
        style = odf.style.Style(name=self.styleName, family='table-row')
        manager.document.automaticstyles.addElement(style)
        style.addElement(rowProps)
        self.parent.rowCount += 1

    def process(self):
        self.styleRow()
        self.row = odf.table.TableRow(stylename=self.styleName)
        self.parent.table.addElement(self.row)
        self.processSubDirectives()


class TableBulkData(directive.RMLDirective):
    signature = rml_flowable.ITableBulkData

    def process(self):
        # Retrieves the text in the bulkData tag.
        lines = [x.strip() for x in self.element.text.splitlines()]
        # Converts the retrieved text into tr and td tags
        for rowData in lines:
            newRow = lxml.etree.Element('tr')
            cells = rowData.split(',')
            for cell in cells:
                newCell = lxml.etree.Element('td')
                newCell.text = cell
                newRow.append(newCell)
            self.parent.element.append(newRow)
        # Removes bulkData object so that recursion loop does not occur
        self.parent.element.remove(self.element)
        # Cheating: reprocess the blockTable again,
        # that we added the rows and columns above
        self.parent.process()


class BlockTable(flowable.Flowable):
    signature = rml_flowable.IBlockTable
    factories = {
        'tr': TableRow,
        'bulkData': TableBulkData,
    }

    def addColumns(self):
        attribs = dict(self.getAttributeValues())
        colWidths = attribs.get('colWidths', [])

        manager = attr.getManager(self)
        for idx in range(self.columns):
            # Create a style for each column
            styleName = manager.getNextStyleName('TableColumn')
            style = odf.style.Style(name=styleName, family='table-column')
            manager.document.automaticstyles.addElement(style)
            colProps = odf.style.TableColumnProperties()
            # Apply the width if available.
            if colWidths:
                try:
                    colWidth = colWidths[idx]
                except IndexError:
                    pass
                else:
                    if (isinstance(colWidth, six.string_types) and
                            colWidth.endswith('%')):
                        colProps.setAttribute('relcolumnwidth',
                                              colWidth[:-1] + '*')
                    else:
                        # PITA: LibreOffice ignores width given in absolute
                        #       measurements like mm, does some relative width
                        #       based on the values
                        colProps.setAttribute('columnwidth', colWidth)
            style.addElement(colProps)

            self.table.addElement(odf.table.TableColumn(stylename=styleName))

    def haveBulkData(self):
        # Checks if we a bulkData tag and dynamically adds colWidths and
        # rowHeights to the parent (blockTable)
        element = self.element.getchildren()[0]
        return element.tag == 'bulkData'

    def process(self):
        # if we have a bulkData tag, let's have first TableBulkData
        # process the data by adding tr and td tags
        # XXX: might be simpler to grasp if this would be done here
        #      and we'd just drop the bulkData child tag
        if not self.haveBulkData():
            self.rowCount = 0
            manager = attr.getManager(self)

            if 'style' in self.element.attrib:
                styleName = self.element.attrib.get('style')
            else:
                styleName = manager.getNextStyleName('Table')
                style = odf.style.Style(name=styleName, family='table')
                manager.document.automaticstyles.addElement(style)
                # XXX: not sure that we always want 100% width
                tableProps = odf.style.TableProperties(relwidth='100%')
                style.addElement(tableProps)

            self.table = odf.table.Table(stylename=styleName)
            if isinstance(self.parent, TableCell):
                # a table in a table
                self.table.setAttribute('issubtable', 'true')

            # ODT doesn't allow tables in list-items
            # handling a blockTable in a ListItem is done with
            # shoobx.rml2odt.list.BlockTableInList
            self.contents.addElement(self.table)

            self.addColumns()
        self.processSubDirectives()

    @lazy.lazy
    def rows(self):
        return len([e for e in self.element.getchildren() if e.tag == 'tr'])

    @lazy.lazy
    def columns(self):
        return max([len([e for e in row.getchildren() if e.tag == 'td'])
                     for row in self.element.getchildren()])


flowable.Flow.factories['blockTable'] = BlockTable
