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


from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special
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
        'linespacing', pt(rmlStyle.leading-rmlStyle.fontSize))
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
        'padding', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'paddingtop', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'paddingbottom', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'paddingleft', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'border', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'bordertop', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'borderbottom', str(rmlStyle.borderPadding))
    paraProps.setAttribute(
        'borderleft', str(rmlStyle.leftIndent))
    paraProps.setAttribute(
        'borderright', str(rmlStyle.rightIndent))
    paraProps.setAttribute(
        'borderlinewidth', str(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthtop', str(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthbottom', str(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthleft', str(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'borderlinewidthright', str(rmlStyle.borderWidth))

    if rmlStyle.backColor is not None:
        paraProps.setAttribute('backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])
    if rmlStyle.borderColor is not None:
        paraProps.setAttribute('backgroundcolor', '#'+rmlStyle.borderColor.hexval()[2:])
 
    # Text Properties
    textProps = odf.style.TextProperties()
    odtStyle.addElement(textProps)

    if rmlStyle.fontName is not None:
        flag = rmlStyle.fontName.find('-')
        if flag == -1:
            fontName = rmlStyle.fontName
        else: 
            fontName = rmlStyle.fontName[:flag]
            transform = rmlStyle.fontName[flag+1:]
            if transform == 'Italic':
                #import pdb; pdb.set_trace()
                textProps.setAttribute('fontstyle', 'italic')
            elif transform == 'Bold':
                textProps.setAttribute('fontweight', 'bold')
            
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=fontName,
                fontfamily=fontName))
        textProps.setAttribute('fontname', fontName)
    textProps.setAttribute('fontsize', rmlStyle.fontSize)
    textProps.setAttribute('texttransform', rmlStyle.textTransform)


    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#'+rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute('backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])
    

def registerListStyle(doc, attributes, rmlStyle, name):
    name = attributes.get('name', 'undefined')
    bulletType = attributes.get('start', 'diamond')
    bulletFormat = attributes.get('bulletFormat', None)
    bulletOffsetY = attributes.get('bulletOffsetY', '0pt')
    bulletDedent = attributes.get('bulletDedent', '50pt')
    fontsize = attributes.get('bulletFontSize', '14pt')
    numType = attributes.get('bulletType', None)
   
    bulletDict = {
     'circle':u'\u2022',
     'square':u'\u25AA',
     'diamond':u'\u2B29',
     'darrowhead':u'\u2304'
     }

    # Declare properties of the list style
    odtStyle = odf.text.ListStyle(name=name)
    listProps = odf.style.ListLevelProperties()

    # listProps.setAttribute('width', '0,15in')
    # listProps.setAttribute('height', '0.15in')
    listProps.setAttribute('minlabelwidth', '0.25in')
    listProps.setAttribute('minlabeldistance','0.15in')
    listProps.setAttribute('textalign', rmlStyle.leftIndent)
    listProps.setAttribute('textalign', rmlStyle.rightIndent)
    #listProps.setAttribute('verticalpos', rmlStyle.bulletOffsetY)
    # XXX: May use this later if need be
    # listProps.setAttribute('spacebefore', '0.15in')

    
  
    if rmlStyle.bulletFontName is not None:
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=rmlStyle.bulletFontName,
                fontfamily=rmlStyle.bulletFontName))
        listProps.setAttribute('fontname', rmlStyle.bulletFontName)
    
    if bulletFormat != None:
        if bulletFormat == '(%s)':
            numbering = odf.text.ListLevelStyleNumber(
                level='1', 
                stylename="Numbering_20_Symbols", 
                numsuffix=")",
                numprefix="(" ,
                numformat=numType)
            numbering.addElement(listProps)
            odtStyle.addElement(numbering)

    else:
        retrievedBullet = bulletDict.get(bulletType, 'circle')
        bullet = odf.text.ListLevelStyleBullet(
            bulletchar = retrievedBullet, 
            level='1', 
            stylename="Standard",
            bulletrelativesize='75%')
        bullet.addElement(listProps)     
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
    textProps = {}
    paraProps = {}

    def process(self):
        attributes = self.element.attrib
        # Loops through all attributes of the blockTableStyle and attempts to 
        # implement them using the correct property 'type'
        for key in attributes:
            if key == "colorName" and isinstance(self, BlockTextColor):
                value = '#' + reportlab.lib.colors.toColor(attributes[key]).hexval()[2:]
                self.parent.tableProps.setAttribute('backgroundcolor', [value]+['text'])

            elif key == 'colorName' and not isinstance(self, BlockTextColor):
                value = '#' + reportlab.lib.colors.toColor(attributes[key]).hexval()[2:]
                self.parent.cellProps.setAttribute('backgroundcolor', [value]+['back'])

            elif key == 'colorNames':
                tempVal = attributes[key].split(" ")
                value = ['#' + reportlab.lib.colors.toColor(x).hexval()[2:] for x in tempVal]
            else:
                value = attributes[key]

            # Takes care of 'length' belonging to different properties
            if key == 'length':
                if isinstance(self, BlockLeftPadding):
                    self.parent.cellProps.setAttribute('paddingleft', value)
                elif isinstance(self, BlockRightPadding):
                    self.parent.cellProps.setAttribute('paddingright', value)
                elif isinstance(self, BlockTopPadding):
                    self.parent.cellProps.setAttribute('paddingtop', value)
                elif isinstance(self, BlockBottomPadding):
                    self.parent.cellProps.setAttribute('paddingbottom', value)
                elif isinstance(self, BlockLeading):
                    self.parent.paraProps.setAttribute('linespacing', value)


            if key in TableStyleCommand.colProps:
                self.parent.colProps.setAttribute(TableStyleCommand.colProps[key], value)

            elif key in TableStyleCommand.textProps:
                if key == 'name':
                    manager = attr.getManager(self)
                    manager.document.fontfacedecls.addElement(
                        odf.style.FontFace(
                            name=value,
                            fontfamily=value))
                self.parent.textProps.setAttribute(TableStyleCommand.textProps[key], value)

            elif key in TableStyleCommand.cellProps:
                self.parent.cellProps.setAttribute(TableStyleCommand.cellProps[key], value)

            elif key in TableStyleCommand.paraProps:
                self.parent.paraProps.setAttribute(TableStyleCommand.paraProps[key], value)

            elif key in TableStyleCommand.tableProps:
                self.parent.tableProps.setAttribute(TableStyleCommand.tableProps[key], value)

            elif key in TableStyleCommand.rowProps:
                # TableColProperties do not support background colors at all
                # TableRowProperties is being used to process both alternating
                # rows and cols colors. Appending either 'row' or 'col' is used 
                # to distinguish between alternating colored rows or cols
                if isinstance(self, BlockColBackground):
                    self.parent.rowProps.setAttribute(TableStyleCommand.rowProps[key], value+['col'])
                elif isinstance(self, BlockRowBackground):
                    self.parent.rowProps.setAttribute(TableStyleCommand.rowProps[key], value+['row'])
            else:
                pass


class BlockFont(TableStyleCommand):
    signature = rml_stylesheet.IBlockFont
    name = 'FONT'
    TableStyleCommand.textProps['name'] = 'fontname'
    TableStyleCommand.textProps['size'] = 'fontsize'
    TableStyleCommand.paraProps['leading'] = 'linespacing'


class BlockLeading(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeading
    name = 'LEADING'


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


class BlockRightPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockRightPadding
    name = 'RIGHTPADDING'


class BlockBottomPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockBottomPadding
    name = 'BOTTOMPADDING'


class BlockTopPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockTopPadding
    name = 'TOPPADDING'


class BlockBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockBackground
    name = 'BACKGROUND'

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
        'blockFont': BlockFont,
        # 'blockLeading': BlockLeading,
        'blockTextColor': BlockTextColor,
        'blockAlignment': BlockAlignment,
        'blockLeftPadding': BlockLeftPadding,
        'blockRightPadding': BlockRightPadding,
        'blockBottomPadding': BlockBottomPadding,
        'blockTopPadding': BlockTopPadding,
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
        self.textProps  = odf.style.TextProperties()
        self.paraProps  = odf.style.ParagraphProperties()
        # Fill style
        self.style.addElement(self.colProps)
        self.style.addElement(self.cellProps)
        self.style.addElement(self.tableProps)
        self.style.addElement(self.rowProps)
        self.style.addElement(self.textProps)
        self.style.addElement(self.paraProps)
        self.processSubDirectives()
        # Add style to the manager
        manager = attr.getManager(self)
        manager.document.automaticstyles.addElement(self.style)


class ListStyle(directive.RMLDirective):
    signature = rml_stylesheet.IListStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', reportlab.lib.styles.ListStyle(name=None))
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        for name, value in kwargs.items():
            setattr(style, name, value)
        attributeDict = self.element.attrib
        document=self.parent.parent.document
        registerListStyle(document, attributeDict, style, name)



class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
        }

