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
import six
import zope.interface

from z3c.rml import attr, directive
from z3c.rml import flowable as rml_flowable

from shoobx.rml2odt import flowable
from shoobx.rml2odt import stylesheet
from shoobx.rml2odt.interfaces import IContentContainer


def _styleCell():
    sc = dict(
        cellProps=odf.style.TableCellProperties(),
        paraProps=odf.style.ParagraphProperties(),
        textProps=odf.style.TextProperties())
    # reportlab vertically aligns cells to the bottom, ODT to the top
    # make sure ODT gets the bottom alignment as default
    sc['cellProps'].setAttribute('verticalalign', 'bottom')
    return sc


def _prepCellStyle(manager, cell):
    # Cell styling
    cell['cellStyleName'] = manager.getNextStyleName('TableCell')
    cell['cellStyle'] = odf.style.Style(
        name=cell['cellStyleName'],
        family='table-cell')
    cell['cellStyle'].addElement(cell['cellProps'])

    # Cell Text styling
    cell['cellContentStyleName'] = manager.getNextStyleName('CellContent')
    cell['contentStyle'] = odf.style.Style(
        name=cell['cellContentStyleName'],
        family='paragraph')
    cell['contentStyle'].addElement(cell['textProps'])
    cell['contentStyle'].addElement(cell['paraProps'])

    manager.document.automaticstyles.addElement(cell['cellStyle'])
    manager.document.automaticstyles.addElement(cell['contentStyle'])


@zope.interface.implementer(IContentContainer)
class TableCell(flowable.Flow):
    signature = rml_flowable.ITableCell

    styleAttributesMapping = {
        'fontName': ('textProps', 'fontname', None),
        'fontSize': ('textProps', 'fontsize', stylesheet.pt),
        'fontColor': ('textProps', 'color', stylesheet.hexColor),
        'leading': ('paraProps', 'linespacing', stylesheet.pt),
        'leftPadding': ('cellProps', 'paddingleft', stylesheet.pt),
        'rightPadding': ('cellProps', 'paddingright', stylesheet.pt),
        'topPadding': ('cellProps', 'paddingtop', stylesheet.pt),
        'bottomPadding': ('cellProps', 'paddingbottom', stylesheet.pt),
        'background': ('cellProps', 'backgroundcolor', stylesheet.hexColor),
        'align': ('paraProps', 'textalign', stylesheet.convertAlignment),
        'vAlign': ('cellProps', 'verticalalign', lambda v: v.lower()),
        # ('LINEBELOW', ('lineBelowThickness', 'lineBelowColor',
        #                'lineBelowCap', 'lineBelowCount', 'lineBelowSpace')),
        # ('LINEABOVE', ('lineAboveThickness', 'lineAboveColor',
        #                'lineAboveCap', 'lineAboveCount', 'lineAboveSpace')),
        # ('LINEBEFORE', ('lineLeftThickness', 'lineLeftColor',
        #                 'lineLeftCap', 'lineLeftCount', 'lineLeftSpace')),
        # ('LINEAFTER', ('lineRightThickness', 'lineRightColor',
        #                'lineRightCap', 'lineRightCount', 'lineRightSpace')),
        # ('HREF', ('href': ('', ''),
        # ('DESTINATION', ('destination': ('', ''),
        }

    def _convertSimpleContent(self, contentStyle):
        # Check whether we need to create a para element.
        # Do we have any children which need a Paragraph?
        haveSub = any([sub.tag in flowable.Paragraph.factories
                       for sub in self.element])
        # Is there text in the element?
        haveText = self.element.text is not None and self.element.text.strip()
        if (not haveText and not haveSub):
            return

        # Create a <para> element.
        para = lxml.etree.Element('para', style=contentStyle)

        # Transfer text.
        # XXX: as it looks reportlab adds newlines in td tags
        #      when there are newlines in the XML!
        para.text = self.element.text
        # Nuke text instead of removing the current element
        self.element.text = None

        # Transfer children.
        for sub in tuple(self.element.getchildren()):
            para.append(sub)

        # Add paragraph to table cell.
        self.element.append(para)

    def _copyCellStyle(self, frm):
        # pretty lame attribute copy, but deepcopy fails
        newCellStyle = _styleCell()
        for prop in ('cellProps', 'paraProps', 'textProps'):
            newCellStyle[prop].attributes = dict(frm[prop].attributes)
        return newCellStyle
    
    def process(self):
        col = len(self.parent.row.childNodes)
        row = self.parent.parent.rowCount - 1

        styleMap = self.parent.parent.styleMap
        cellStyle = styleMap[col][row]

        attrs = dict(self.getAttributeValues(ignore=('content',)))
        if attrs:
            # the cell has local formatting, need to patch that into the style
            cellStyle = self._copyCellStyle(cellStyle)

            for aname, avalue in attrs.items():
                if aname in self.styleAttributesMapping:
                    targetProp, targetAttr, converter = \
                        self.styleAttributesMapping[aname]
                    if converter is not None:
                        avalue = converter(avalue)
                    cellStyle[targetProp].setAttribute(targetAttr, avalue)

            manager = attr.getManager(self)
            _prepCellStyle(manager, cellStyle)

        spanMap = self.parent.parent.spanMap
        cellspan = spanMap[col][row]
        if cellspan:
            if isinstance(cellspan, dict):
                kw = cellspan
            else:
                kw = {}
            self.cell = odf.table.TableCell(
                stylename=cellStyle['cellStyleName'],
                valuetype='string', **kw)
            self._convertSimpleContent(cellStyle['cellContentStyleName'])
            process = True
        elif cellspan is False:
            self.cell = odf.table.CoveredTableCell()
            # do NOT add any content to a CoveredTableCell
            process = False

        self.parent.row.addElement(self.cell)
        self.contents = self.cell
        if process:
            super(TableCell, self).process()

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
        # processed in self.haveBlockTableStyle
        # 'blockTableStyle': stylesheet.BlockTableStyle
    }

    def _getStartEndPos(self, attrs):
        start_col, start_row = attrs['start']
        end_col, end_row = attrs['stop']

        # negative indexes are like python lists, count from right
        # also sort on the index
        cols = sorted([col if col >= 0 else self.columns+col
                       for col in [start_col, end_col]])
        start_col = cols[0]
        end_col = cols[1]
        rows = sorted([row if row >= 0 else self.rows+row
                       for row in [start_row, end_row]])
        start_row = rows[0]
        end_row = rows[1]

        return start_col, start_row, end_col, end_row

    def _doZebraRows(self, stylemap, attrs):
        start_col, start_row, end_col, end_row = self._getStartEndPos(attrs)
        colors = attrs['cellProps']['backgroundcolors']
        for col in range(start_col, end_col+1):
            idx = 0
            for row in range(start_row, end_row+1):
                cell = stylemap[col][row]
                if colors[idx]:
                    cell['cellProps'].setAttribute(
                        'backgroundcolor', colors[idx])
                idx += 1
                if idx >= len(colors):
                    idx = 0

    def _doZebraCols(self, stylemap, attrs):
        start_col, start_row, end_col, end_row = self._getStartEndPos(attrs)
        colors = attrs['cellProps']['backgroundcolors']
        idx = 0
        for col in range(start_col, end_col+1):
            for row in range(start_row, end_row+1):
                cell = stylemap[col][row]
                if colors[idx]:
                    cell['cellProps'].setAttribute(
                        'backgroundcolor', colors[idx])
            idx += 1
            if idx >= len(colors):
                idx = 0

    def _doStyleMap(self, stylemap, attrs):
        start_col, start_row, end_col, end_row = self._getStartEndPos(attrs)
        for col in range(start_col, end_col+1):
            for row in range(start_row, end_row+1):
                cell = stylemap[col][row]

                for attrKey in ('cellProps', 'paraProps', 'textProps'):
                    for aname, avalue in attrs[attrKey].items():
                        cell[attrKey].setAttribute(aname, avalue)

    def getStyleMap(self):
        # prepare a map of styles for each cell in the table
        stylemap = [
            [_styleCell()
             for r in range(self.rows)] for c in range(self.columns)]
        table_style = self.getAttributeValues(select=['style'])
        if table_style:
            table_style = table_style[0][1]

            for name, styleCommands in table_style.collector.items():
                for styleCommand in styleCommands:
                    attrs = styleCommand.getStyleProps()

                    if name == 'blockRowBackground':
                        self._doZebraRows(stylemap, attrs)
                    elif name == 'blockColBackground':
                        self._doZebraCols(stylemap, attrs)
                    else:
                        self._doStyleMap(stylemap, attrs)

        manager = attr.getManager(self)
        for row in stylemap:
            for cell in row:
                _prepCellStyle(manager, cell)

        return stylemap

    def getSpanMap(self):
        # prepare a map of spanned cells
        # ODF expects `numbercolumnsspanned` or `numberrowsspanned` on
        # the cell that spans more columns/rows
        # ODF also expects `table:covered-table-cell`
        # instead of a table:table-cell when a cell should not be 'displayed'
        spanmap = [
            [True for r in range(self.rows)] for c in range(self.columns)]
        table_style = self.getAttributeValues(select=['style'])
        if table_style:
            table_style = table_style[0][1]

            for blockspan in table_style.collector['blockSpan']:
                attrs = dict(blockspan.getAttributeValues())
                start_col, start_row, end_col, end_row = self._getStartEndPos(attrs)

                columnsspanned = end_col - start_col + 1
                rowsspanned = end_row - start_row + 1

                if columnsspanned == 1 and rowsspanned == 1:
                    continue

                # mark all spanned cells
                for col in range(start_col, end_col+1):
                    for row in range(start_row, end_row+1):
                        spanmap[col][row] = False
                # only the top left cell needs the span info
                spaninfo = {}
                # and only spans > 1 need to be added to the ODF
                if columnsspanned > 1:
                    spaninfo['numbercolumnsspanned'] = columnsspanned
                if rowsspanned > 1:
                    spaninfo['numberrowsspanned'] = rowsspanned
                spanmap[start_col][start_row] = spaninfo
        return spanmap

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
        for element in self.element.getchildren():
            if element.tag == 'bulkData':
                return True
        return False

    def haveBlockTableStyle(self):
        for element in self.element.getchildren():
            if element.tag == 'blockTableStyle':
                bts = stylesheet.BlockTableStyle(element, self)
                bts.process()
                self.element.attrib['style'] = element.attrib['id']

    def process(self):
        # if we have a bulkData tag, let's have first TableBulkData
        # process the data by adding tr and td tags
        # XXX: might be simpler to grasp if this would be done here
        #      and we'd just drop the bulkData child tag
        if not self.haveBulkData():
            self.haveBlockTableStyle()
            self.spanMap = self.getSpanMap()
            self.styleMap = self.getStyleMap()
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
