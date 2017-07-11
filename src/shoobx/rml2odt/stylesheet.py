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
"""Style Related Element Processing
"""
import copy
import odf.style
import odf.text
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus

from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from z3c.rml import stylesheet as rml_stylesheet




RML2ODT_ALIGNMENTS = {
    TA_LEFT: 'left',
    TA_CENTER: 'center',
    TA_RIGHT: 'right',
    TA_JUSTIFY: 'justify',
}

def pt(pt):
    return '%ipt' %pt


class Initialize(directive.RMLDirective):
    signature = rml_stylesheet.IInitialize
    factories = {
        'name': special.Name,
        'alias': special.Alias,
        }




def registerParagraphStyle(doc, name, rmlStyle):

    if 'style.' in name:
        name = name[6:]



    odtStyle = odf.style.Style(name=name, family='paragraph')
    doc.automaticstyles.addElement(odtStyle)

    # Paragraph Properties

    paraProps = odf.style.ParagraphProperties()
    odtStyle.addElement(paraProps)
    paraProps.setAttribute(
        'linespacing', pt(rmlStyle.leading))
    paraProps.setAttribute(
        'textalign', RML2ODT_ALIGNMENTS[rmlStyle.alignment])
    if rmlStyle.justifyLastLine:
        paraProps.setAttribute(
            'textalignlast', 'justify')
    paraProps.setAttribute(
        'textindent', pt(rmlStyle.firstLineIndent))
    paraProps.setAttribute(
        'widows', int(rmlStyle.allowWidows))
    paraProps.setAttribute(
        'orphans', int(rmlStyle.allowOrphans))
    paraProps.setAttribute(
        'marginleft', pt(rmlStyle.leftIndent))
    paraProps.setAttribute(
        'marginright', pt(rmlStyle.rightIndent))
    paraProps.setAttribute(
        'margintop', pt(rmlStyle.spaceBefore))
    paraProps.setAttribute(
        'marginbottom', pt(rmlStyle.spaceAfter))
    paraProps.setAttribute(
        'pagenumber', pt(rmlStyle.pageNumber))
    paraProps.setAttribute(
        'borderlinewidth', pt(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthtop', pt(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthbottom', pt(rmlStyle.borderWidth))

    if rmlStyle.padding:
        paraProps.setAttribute(
            'paddingtop', 'paddingbottom', 'paddingleft', 'paddingright')
    if rmlStyle.border is not None:
        paraProps.setAttribute(
            'bordertop', 'borderbottom', 'borderleft', 'borderright')

    if rmlStyle.backColor is not None:
        paraProps.setAttribute('backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])
    
 

    # Text Properties

    textProps = odf.style.TextProperties()
    odtStyle.addElement(textProps)

         
    if rmlStyle.fontName is not None:
        
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=rmlStyle.fontName,
                fontfamily=rmlStyle.fontName))
        textProps.setAttribute('fontname', rmlStyle.fontName)
    textProps.setAttribute('fontsize', rmlStyle.fontSize)
    textProps.setAttribute('texttransform', rmlStyle.textTransform)


    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#'+rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute('backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])
    




def registerListStyle(doc, attributes):


    name = attributes.get('name', 'undefined')
    bulletType = attributes.get('start', 'disc')
    fontname = attributes.get('bulletfontname', 'Arial')
    bulletFormat = attributes.get('bulletformat', "%s:")
    textalign = attributes.get('textalign', 'left')
    fontsize = attributes.get('bulletFontSize', '14pt')
    
    bulletDict = {
     'disc':u'\u2022',
     'square':u'\u25AA',
     'diamond':u'\u2B29',
     'arrowhead':u'\u2B9E'
     }



    # Declare properties of the list style
    
    odtStyle = odf.text.ListStyle(name=name)
    listProps = odf.style.ListLevelProperties()
    listProps.setAttribute('spacebefore', '0.15in')
    listProps.setAttribute('width', name)
    listProps.setAttribute('height', name)
    listProps.setAttribute('textalign', RML2ODT_ALIGNMENTS)
    listProps.setAttribute('minlabelwidth', '0.25in')
    listProps.setAttribute('minlabeldistance','0.15in')
    listProps.setAttribute('fontname', fontname)
    # Create new bullet object
    retrievedBullet = bulletDict.get(bulletType, 'disc')

    bullet = odf.text.ListLevelStyleBullet(
         bulletchar = retrievedBullet, 
         level='1', 
         stylename="Standard",
         bulletrelativesize='75%')

    # Add properties to created bullet style object
    bullet.addElement(listProps)     
    # Add bullet object to created style
    odtStyle.addElement(bullet)

    doc.automaticstyles.addElement(odtStyle)
    

class ParagraphStyle(directive.RMLDirective):
    signature = rml_stylesheet.IParagraphStyle    

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', SampleStyleSheet['Normal'])
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name
        for attrName, attrValue in kwargs.items():
            setattr(style, attrName, attrValue)
        document = self.parent.parent.document
        registerParagraphStyle(document, name, style)


class TableStyleCommand(directive.RMLDirective):
    name = None
    cellProps = {}
    colProps = {}
    tableProps = {}
    rowProps = {}

    def process(self):
        cellProps = TableStyleCommand.cellProps
        colProps = TableStyleCommand.colProps
        rowProps = TableStyleCommand.rowProps
        tableProps = TableStyleCommand.tableProps

        attributes = self.element.attrib

        # Loops through all attributes of the blockTableStyle and attempts to 
        # implement them using the correct property 'type'
        for key in attributes:

            if 'color' in key:
                # Takes care of cases where multiple colors are given
                tempVal = attributes[key].split(" ")
                value = ['#' + reportlab.lib.colors.toColor(x).hexval()[2:] for x in tempVal]
            else:
                value = attributes[key]


            if key in colProps:
                self.parent.colProps.setAttribute(colProps[key], value)

            elif key in cellProps:
                # Retrieves the singular color for backgroundcolor
                if 'color' in key:
                    self.parent.cellProps.setAttribute(cellProps[key], value[0])
                else:
                    self.parent.cellProps.setAttribute(cellProps[key], value)

            elif key in tableProps:
                self.parent.tableProps.setAttribute(tableProps[key], value)

            elif key in rowProps:
                # TableColProperties do not support background colors at all
                # TableRowProperties is being used to process both alternating
                # rows and cols colors. Appending either 'row' or 'col' is used 
                # to distinguish between alternating colored rows or cols
                if isinstance(self, BlockColBackground):
                    self.parent.rowProps.setAttribute(rowProps[key], value+['col'])
                elif isinstance(self, BlockRowBackground):
                    self.parent.rowProps.setAttribute(rowProps[key], value+['row'])
            else:
                pass


class BlockFont(TableStyleCommand):
    signature = rml_stylesheet.IBlockFont
    name = 'FONT'


class BlockLeading(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeading
    name = 'LEADING'
    # XXX: FIGURE IT OUT - Probably a regular style linespacing attribute
    # TableStyleCommand.cellProps['length'] = 'FIGUREITOUT'


class BlockTextColor(TableStyleCommand):
    signature = rml_stylesheet.IBlockTextColor
    name = 'TEXTCOLOR'


class BlockAlignment(TableStyleCommand):
    signature = rml_stylesheet.IBlockAlignment
    name = 'ALIGNMENT'
    TableStyleCommand.tableProps['value'] = 'align'


class BlockLeftPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeftPadding
    name = 'LEFTPADDING'
    TableStyleCommand.cellProps['length'] = 'leftpadding'


class BlockRightPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockRightPadding
    name = 'RIGHTPADDING'
    TableStyleCommand.cellProps['length'] = 'rightpadding'


class BlockBottomPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockBottomPadding
    name = 'BOTTOMPADDING'
    TableStyleCommand.cellProps['length'] = 'bottompadding'


class BlockTopPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockTopPadding
    name = 'TOPPADDING'
    TableStyleCommand.cellProps['length'] = 'paddingtop'


class BlockBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockBackground
    name = 'BACKGROUND'
    TableStyleCommand.cellProps['colorName'] = 'backgroundcolor'

    # def process(self):
    #     args = [self.name]
        # if 'colorsByRow' in self.element.keys():
        #     args = [BlockRowBackground.name]
        # elif 'colorsByCol' in self.element.keys():
        #     args = [BlockColBackground.name]
        # attributes = self.getAttributeValues(valuesOnly=True)
        # self.parent.style.add(*args)


class BlockRowBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockRowBackground
    name = 'ROWBACKGROUNDS'
    TableStyleCommand.rowProps['colorNames'] = 'backgroundcolor'


class BlockColBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockColBackground
    name = 'COLBACKGROUNDS'
    TableStyleCommand.rowProps['colorNames'] = 'backgroundcolor'



class BlockValign(TableStyleCommand):
    signature = rml_stylesheet.IBlockValign
    name = 'VALIGN'


class BlockSpan(TableStyleCommand):
    signature = rml_stylesheet.IBlockSpan
    name = 'SPAN'


class LineStyle(TableStyleCommand):
    signature = rml_stylesheet.ILineStyle

    def process(self):
        name = self.getAttributeValues(select=('kind',), valuesOnly=True)[0]
        args = [name]
        args += self.getAttributeValues(ignore=('kind',), valuesOnly=True,
                                        includeMissing=True)
        self.parent.style.add(*args)


class BlockTableStyle(directive.RMLDirective):
    signature = rml_stylesheet.IBlockTableStyle

    factories = {
        # 'blockFont': BlockFont,
        # 'blockLeading': BlockLeading,
        # 'blockTextColor': BlockTextColor,
        'blockAlignment': BlockAlignment,
        # 'blockLeftPadding': BlockLeftPadding,
        # 'blockRightPadding': BlockRightPadding,
        # 'blockBottomPadding': BlockBottomPadding,
        # 'blockTopPadding': BlockTopPadding,
        'blockBackground': BlockBackground,
        'blockRowBackground': BlockRowBackground,
        'blockColBackground': BlockColBackground,
        # 'blockValign': BlockValign,
        # 'blockSpan': BlockSpan,
        # 'lineStyle': LineStyle,
        }

    def process(self):
        kw = dict(self.getAttributeValues())
        self.styleID = kw.pop('id')
        # Create Style
        self.style = odf.style.Style(name=self.styleID, family='table')
        # Create style properties
        self.colProps   = odf.style.TableColumnProperties()
        self.cellProps  = odf.style.TableCellProperties()
        self.tableProps = odf.style.TableProperties()
        self.rowProps   = odf.style.TableRowProperties()
        # Fill style
        self.style.addElement(self.colProps)
        self.style.addElement(self.cellProps)
        self.style.addElement(self.tableProps)
        self.style.addElement(self.rowProps)
        self.processSubDirectives()
        # Add style to the manager
        manager = attr.getManager(self)
        manager.document.automaticstyles.addElement(self.style)


class ListStyle(directive.RMLDirective):
    signature = rml_stylesheet.IListStyle

    def process(self):
        attributeDict = self.element.attrib
        document=self.parent.parent.document
        registerListStyle(document, attributeDict)


class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
        }

