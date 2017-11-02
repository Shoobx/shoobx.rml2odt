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
import six

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
    return '%ipt' % pt


class Initialize(directive.RMLDirective):
    signature = rml_stylesheet.IInitialize
    factories = {
        'name': special.Name,
        'alias': special.Alias,
    }


FONT_MAP = {
    'symbol': 'Symbol',
    'zapfdingbats': 'ZapfDingbats',
    'helvetica': 'Arial',
    'times': 'Times New Roman',
    'courier': 'Courier',
    'garamond': 'Adobe Garamond Pro',
}


def rmlFont2odfFont(font):
    # Maps between RML/Postscript font names and ODT/LibreOffice names
    name = font.lower().split('-')[0]
    return FONT_MAP.get(name, font)


def registerParagraphStyle(doc, name, rmlStyle):
    if 'style.' in name:
        name = name[6:]

    odtStyle = odf.style.Style(name=name, family='paragraph')
    doc.automaticstyles.addElement(odtStyle)

    # Paragraph Properties
    paraProps = odf.style.ParagraphProperties()
    odtStyle.addElement(paraProps)
    if name == "sig-small-logo":
        paraProps.setAttribute('lineheight', "0.14in")
    else:
        paraProps.setAttribute('linespacing',
                               pt(rmlStyle.leading - rmlStyle.fontSize))
    if name == "Small":
        paraProps.setAttribute('textalign', 'left')
    else:
        paraProps.setAttribute('textalign',
                               RML2ODT_ALIGNMENTS[rmlStyle.alignment])
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

    if rmlStyle.backColor is not None:
        paraProps.setAttribute(
            'backgroundcolor', '#' + rmlStyle.backColor.hexval()[2:])

    if rmlStyle.borderPadding is not None:

        paraProps.setAttribute('padding', '%spt' % rmlStyle.borderPadding)

    if rmlStyle.borderWidth:
        if rmlStyle.borderColor:
            color = rmlStyle.borderColor.hexval()[2:]
        else:
            # Default to black if no color is specified. I can't find any
            # docs on how attributes like this are supposed to work, so...
            color = "000000"
        paraProps.setAttribute('border', "%spt solid #%s" % (
            rmlStyle.borderWidth, color))

    # reportlab styles doesn't have guaranteed attributes, so we need hasattr
    if getattr(rmlStyle, 'keepWithNext', False):
        paraProps.setAttribute('keepwithnext', 'always')

    # Text Properties
    textProps = odf.style.TextProperties()
    odtStyle.addElement(textProps)

    if rmlStyle.fontName is not None:
        flag = rmlStyle.fontName.find('-')
        if flag != -1:
            transform = rmlStyle.fontName[flag + 1:]
            if transform == 'Italic':
                textProps.setAttribute('fontstyle', 'italic')
            elif transform == 'Bold':
                textProps.setAttribute('fontweight', 'bold')
            elif transform == 'BoldItalic':
                textProps.setAttribute('fontweight', 'bold')
                textProps.setAttribute('fontstyle', 'italic')

        odf_font_name = rmlFont2odfFont(rmlStyle.fontName)
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=odf_font_name,
                fontfamily=odf_font_name))
        textProps.setAttribute('fontname', odf_font_name)
    textProps.setAttribute('fontsize', rmlStyle.fontSize)
    textProps.setAttribute('texttransform', rmlStyle.textTransform)

    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#' + rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute(
            'backgroundcolor', '#' + rmlStyle.backColor.hexval()[2:])


def RegisterListStyle(doc, attributes, rmlStyle, name):
    name = attributes.get('name', 'undefined')
    bulletType = attributes.get('start')
    bulletFormat = attributes.get('bulletFormat')
    bulletOffsetY = attributes.get('bulletOffsetY', '0pt')
    bulletDedent = attributes.get('bulletDedent', '50pt')
    numType = attributes.get('bulletType')

    bulletDict = {
        'bulletchar': u'\u2022',
        'circle': u'\u25cf',
        'square': u'\u25AA',
        'diamond': u'\u2B29',
        'darrowhead': u'\u2304',
        'rarrowhead': u'\u27a4'
    }

    x = reportlab.lib.styles.ListStyle.defaults

    # Declare properties of the list style
    odtStyle = odf.text.ListStyle(name=name)
    listProps = odf.style.ListLevelProperties()

    listProps.setAttribute('width', None)
    listProps.setAttribute('height', None)
    listProps.setAttribute('minlabelwidth', '0.25in')
    listProps.setAttribute('minlabeldistance', '0.15in')
    listProps.setAttribute('textalign', x.get('bulletAlign'))

    if rmlStyle.bulletFontName is not None:
        odf_font_name = rmlFont2odfFont(rmlStyle.bulletFontName)
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=odf_font_name,
                fontfamily=odf_font_name))
        listProps.setAttribute('fontname', odf_font_name)

    retrievedBullet = bulletDict.get(bulletType)

    if bulletFormat is not None:
        if bulletFormat == '(%s)': # Why limit to only (%s)? Lazy.
            numbering = odf.text.ListLevelStyleNumber(
                level='1',
                stylename="Numbering_20_Symbols",
                numsuffix=")",
                numprefix="(",
                numformat=numType)
            numbering.addElement(listProps)
            odtStyle.addElement(numbering)
    elif retrievedBullet is None:
        numbering = odf.text.ListLevelStyleNumber(
            level='1',
            stylename="Numbering_20_Text",
            numsuffix='',
            numprefix=bulletType,
            numformat='')
        numbering.addElement(listProps)
        odtStyle.addElement(numbering)
    else:
        bullet = odf.text.ListLevelStyleBullet(
            bulletchar=retrievedBullet,
            level='1',
            stylename="Standard",
            bulletrelativesize='75%')
        bullet.addElement(listProps)
        odtStyle.addElement(bullet)

    doc.automaticstyles.addElement(odtStyle)


class ParagraphStyle(directive.RMLDirective):
    signature = rml_stylesheet.IParagraphStyle

    def adjustAttributeValues(self, style, parentName):
        try:
            parentElem = self.parent.parent.document.getStyleByName(
                six.text_type(parentName))
        except AssertionError:
            # The style doesn't exist in the document
            return style

        paraProps = [x for x in parentElem.childNodes
                     if 'paragraph' in x.tagName][0]
        textProps = [x for x in parentElem.childNodes
                     if 'text' in x.tagName][0]

        textPropsMapper = {
            'font-name': 'fontName',
            'text-transform': 'textTransform',
            'font-size': 'fontSize'
        }
        paraPropsMapper = {
            # 'margin-right':'rightIndent',
            # 'line-spacing':,
            # 'margin-top':'spaceBefore',
            # 'text-align':'alignment',
            'orphans': 'allowOrphans',
            # 'margin-left':'leftIndent',
            # 'margin-bottom':'spaceAfter',
            'padding': 'borderPadding',
            # 'text-indent':'firstLineIndent',
            'widows': 'allowWidows'
        }

        for attrib in textProps.attributes:
            desiredAttribute = str(attrib[1])
            value = textProps.attributes[attrib]
            try:
                value = float(value)
            except ValueError:
                value = value
            if desiredAttribute in textPropsMapper:
                setattr(style, textPropsMapper[desiredAttribute], value)

        for attrib in paraProps.attributes:
            desiredAttribute = str(attrib[1])
            value = paraProps.attributes[attrib]
            try:
                value = float(value)
            except ValueError:
                value = value
            if desiredAttribute in paraPropsMapper:
                setattr(style, paraPropsMapper[desiredAttribute], value)
        return style

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', SampleStyleSheet['Normal'])
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name
        document = self.parent.parent.document
        if name == 'Normal':
            defaultNormalStyle = self.parent.parent.document.getStyleByName(
                u'Normal')
            self.parent.parent.document.automaticstyles.removeChild(
                defaultNormalStyle)

        style = self.adjustAttributeValues(style, parent.name)

        for attrName, attrValue in kwargs.items():
            setattr(style, attrName, attrValue)
        registerParagraphStyle(document, name, style)
        attr.getManager(self).styles[name] = style


class TableStyleCommand(directive.RMLDirective):
    name = None
    cellProps = {}
    colProps = {}
    tableProps = {}
    rowProps = {}
    textProps = {}
    paraProps = {}

    def process(self):
        raise NotImplementedError(self.__class__)


class BlockFont(TableStyleCommand):
    signature = rml_stylesheet.IBlockFont
    name = 'FONT'
    attrMapping = {
        'name':'fontname',
        'size':'fontsize',
        'leading': 'linespacing',
    }

    def process(self):
        attrs = dict(self.getAttributeValues())
        odf_font_name = rmlFont2odfFont(attrs['name'])
        manager = attr.getManager(self)
        manager.document.fontfacedecls.addElement(
            odf.style.FontFace(
                name=odf_font_name,
                fontfamily=odf_font_name))

        for key, val in attrs.items():
            if key == 'name':
                self.parent.textProps.setAttribute(
                    'fontname', val)
            elif key == 'size':
                self.parent.textProps.setAttribute(
                    'fontsize', '%spt' % val)
            elif key == 'leading':
                self.parent.paraProps.setAttribute(
                    'linespacing', '%spt' % val)


class BlockLeading(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeading
    name = 'LEADING'


class BlockTextColor(TableStyleCommand):
    signature = rml_stylesheet.IBlockTextColor
    name = 'TEXTCOLOR'

    def process(self):
        attrs = dict(self.getAttributeValues())
        hexcolor = '#%s' % attrs['colorName'].hexval()[2:]
        # Yes, magically, if you set the background color to
        # ['#color', 'text'] it sets the foreground text color!
        self.parent.tableProps.setAttribute(
            'backgroundcolor', [hexcolor] + ['text'])


class BlockAlignment(TableStyleCommand):
    signature = rml_stylesheet.IBlockAlignment
    name = 'ALIGNMENT'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.tableProps.setAttribute(
            'align', attrs['value'].lower())


class BlockLeftPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeftPadding
    name = 'LEFTPADDING'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.cellProps.setAttribute(
            'paddingleft', '%spt' % attrs['length'])


class BlockRightPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockRightPadding
    name = 'RIGHTPADDING'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.cellProps.setAttribute(
            'paddingright', '%spt' % attrs['length'])


class BlockBottomPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockBottomPadding
    name = 'BOTTOMPADDING'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.cellProps.setAttribute(
            'paddingbottom', '%spt' % attrs['length'])


class BlockTopPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockTopPadding
    name = 'TOPPADDING'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.cellProps.setAttribute(
            'paddingtop', '%spt' % attrs['length'])


class BlockBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockBackground
    name = 'BACKGROUND'

    def process(self):
        attrs = dict(self.getAttributeValues())
        hexcolor = '#%s' % attrs['colorName'].hexval()[2:]

        self.parent.cellProps.setAttribute(
            'backgroundcolor', [hexcolor] + ['back'])


class BlockRowBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockRowBackground
    name = 'ROWBACKGROUNDS'

    def process(self):
        attrs = dict(self.getAttributeValues())
        colors = ['#%s' % col.hexval()[2:] for col in attrs['colorNames']]
        self.parent.rowProps.setAttribute(
            'backgroundcolor', colors + ['row'])


class BlockColBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockColBackground
    name = 'COLBACKGROUNDS'

    def process(self):
        attrs = dict(self.getAttributeValues())
        colors = ['#%s' % col.hexval()[2:] for col in attrs['colorNames']]
        self.parent.rowProps.setAttribute(
            'backgroundcolor', colors + ['col'])


class BlockValign(TableStyleCommand):
    signature = rml_stylesheet.IBlockValign
    name = 'VALIGN'

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.cellProps.setAttribute(
            'verticalalign', attrs['value'].lower())


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
        'blockValign': BlockValign,
        # 'blockSpan': BlockSpan,
        # lineStyle': LineStyle,
    }

    def process(self):
        kw = dict(self.getAttributeValues())
        self.styleID = kw.pop('id')
        # Create Style
        self.style = odf.style.Style(name=self.styleID, family='table')
        # Create style properties
        self.colProps = odf.style.TableColumnProperties()
        self.cellProps = odf.style.TableCellProperties()
        self.tableProps = odf.style.TableProperties()
        self.rowProps = odf.style.TableRowProperties()
        self.textProps = odf.style.TextProperties()
        self.paraProps = odf.style.ParagraphProperties()
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
        manager.styles[self.styleID] = self.style


class ListStyle(directive.RMLDirective):
    signature = rml_stylesheet.IListStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        # I do not know the purpose of using a temporary reportlab style here.
        # /regebro
        parent = kwargs.pop(
            'parent', reportlab.lib.styles.ListStyle(name=None))
        style = copy.deepcopy(parent)
        for name, value in kwargs.items():
            setattr(style, name, value)
        attributeDict = dict(self.getAttributeValues())
        document = self.parent.parent.document
        RegisterListStyle(document, attributeDict, style, name)
        attr.getManager(self).styles[style.name] = style


class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
    }
