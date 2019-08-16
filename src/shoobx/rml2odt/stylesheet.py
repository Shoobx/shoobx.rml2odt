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
import lazy
import odf.style
import odf.text
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
import six
from collections import defaultdict

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from z3c.rml import attr, directive, SampleStyleSheet, special
from z3c.rml import stylesheet as rml_stylesheet

RML2ODT_ALIGNMENTS = {
    TA_LEFT: 'left',
    TA_CENTER: 'center',
    TA_RIGHT: 'right',
    TA_JUSTIFY: 'justify',
}


def pt(pt):
    return '%spt' % pt


def hexColor(color):
    if color is None:
        return color
    return '#%s' % color.hexval()[2:]


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

    if getattr(rmlStyle, 'underline', False):
        textProps.setAttribute('textunderlinetype', 'single')
    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#' + rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute(
            'backgroundcolor', '#' + rmlStyle.backColor.hexval()[2:])

    return odtStyle


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


class SpanStyle(ParagraphStyle):
    signature = rml_stylesheet.ISpanStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        name = kwargs.get('name')
        super(SpanStyle, self).process()
        self.parent.parent.document.getStyleByName(
            six.text_type(name)
        ).setAttribute('family', 'text')





class TableStyleCommand(directive.RMLDirective):
    collectorKey = None

    def process(self):
        self.parent.collector[self.collectorKey].append(self)

    @lazy.lazy
    def _cachedAttributeValues(self):
        return dict(self.getAttributeValues())

    def getStyleProps(self):
        attrs = self._cachedAttributeValues

        result = dict(
            start=attrs['start'],
            stop=attrs['stop'],
            textProps={},
            paraProps={},
            cellProps={},
        )
        return result


class BlockFont(TableStyleCommand):
    signature = rml_stylesheet.IBlockFont
    collectorKey = 'blockFont'

    def getStyleProps(self):
        result = super(BlockFont, self).getStyleProps()

        attrs = self._cachedAttributeValues
        for key, val in attrs.items():
            if key == 'name':
                result['textProps']['fontname'] = val
            elif key == 'size':
                result['textProps']['fontsize'] = pt(val)
            elif key == 'leading':
                result['paraProps']['linespacing'] = pt(val)

        return result


class BlockLeading(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeading
    collectorKey = 'blockLeading'

    def getStyleProps(self):
        result = super(BlockLeading, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['paraProps']['linespacing'] = pt(attrs['length'])
        return result


class BlockTextColor(TableStyleCommand):
    signature = rml_stylesheet.IBlockTextColor
    collectorKey = 'blockTextColor'

    def getStyleProps(self):
        result = super(BlockTextColor, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['textProps']['color'] = hexColor(attrs['colorName'])
        return result


def convertAlignment(value):
    value = value.lower()
    if value == 'decimal':
        # ODT has no decimal alignment, our best chance is right
        value = 'right'
    if value == 'centre':
        value == 'center'
    return value


class BlockAlignment(TableStyleCommand):
    signature = rml_stylesheet.IBlockAlignment
    collectorKey = 'blockAlignment'

    def getStyleProps(self):
        result = super(BlockAlignment, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['paraProps']['textalign'] = convertAlignment(attrs['value'])

        return result


class BlockLeftPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeftPadding
    collectorKey = 'blockLeftPadding'

    def getStyleProps(self):
        result = super(BlockLeftPadding, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['paddingleft'] = pt(attrs['length'])
        return result


class BlockRightPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockRightPadding
    collectorKey = 'blockRightPadding'

    def getStyleProps(self):
        result = super(BlockRightPadding, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['paddingright'] = pt(attrs['length'])
        return result


class BlockBottomPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockBottomPadding
    collectorKey = 'blockBottomPadding'

    def getStyleProps(self):
        result = super(BlockBottomPadding, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['paddingbottom'] = pt(attrs['length'])
        return result


class BlockTopPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockTopPadding
    collectorKey = 'blockTopPadding'

    def getStyleProps(self):
        result = super(BlockTopPadding, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['paddingtop'] = pt(attrs['length'])
        return result


class BlockBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockBackground
    collectorKey = 'blockBackground'

    def getStyleProps(self):
        result = super(BlockBackground, self).getStyleProps()

        attrs = self._cachedAttributeValues
        if 'colorName' in attrs:
            result['cellProps']['backgroundcolor'] = \
                hexColor(attrs['colorName'])
        if 'colorsByRow' in attrs:
            result['cellProps']['backgroundcolors'] = \
                [hexColor(cn) for cn in attrs['colorsByRow']]
        if 'colorsByCol' in attrs:
            result['cellProps']['backgroundcolors'] = \
                [hexColor(cn) for cn in attrs['colorsByCol']]

        return result

    def process(self):
        attrs = self._cachedAttributeValues
        # since colorsByRow and colorsByCol should act as
        # blockRowBackground and blockColBackground, let's do a tag translation
        # here, e.g.:
        # <blockBackground colorsByRow="0xD0FFD0;None"
        #   start="0,1" stop="-1,-1"/>
        if 'colorsByRow' in attrs:
            self.collectorKey = 'blockRowBackground'
        if 'colorsByCol' in attrs:
            self.collectorKey = 'blockColBackground'
        return super(BlockBackground, self).process()


class BlockRowBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockRowBackground
    collectorKey = 'blockRowBackground'

    def getStyleProps(self):
        result = super(BlockRowBackground, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['backgroundcolors'] = [
            hexColor(cn) for cn in attrs['colorNames']]
        return result


class BlockColBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockColBackground
    collectorKey = 'blockColBackground'

    def getStyleProps(self):
        result = super(BlockColBackground, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['backgroundcolors'] = [
            hexColor(cn) for cn in attrs['colorNames']]
        return result


class BlockValign(TableStyleCommand):
    signature = rml_stylesheet.IBlockValign
    collectorKey = 'blockValign'

    def getStyleProps(self):
        result = super(BlockValign, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['cellProps']['verticalalign'] = attrs['value'].lower()
        return result


class BlockSpan(TableStyleCommand):
    signature = rml_stylesheet.IBlockSpan
    collectorKey = 'blockSpan'


def convertLineStyle(attrs):
    # ODT line styles discovered by trying:
    # solid, dotted, dashed, fine-dashed, dash-dot, dash-dot-dot,
    # double, double-thin
    # there are plenty left
    if attrs.get('count') == 2:
        style = 'double'
    else:
        style = 'solid'  # by default
        dash = attrs.get('dash')
        if dash:
            # ohwell do some magic, there's no such custom border in ODT
            if len(dash) == 2:
                if dash[0] == dash[1]:
                    if dash[0] in (1, 2):
                        style = 'dotted'
                    elif dash[0] in (3, 4):
                        style = 'fine-dashed'
                    else:
                        style = 'dashed'
                else:
                    style = 'dash-dot'
            else:
                # what? dash-dot-dot?
                pass

    parts = []
    if attrs.get('thickness'):
        parts.append(pt(attrs.get('thickness')))
    else:
        parts.append('1pt')
    parts.append(style)
    if attrs.get('colorName'):
        parts.append(hexColor(attrs['colorName']))

    return ' '.join(parts)


class LineStyle(TableStyleCommand):
    signature = rml_stylesheet.ILineStyle
    collectorKey = 'lineStyle'

    kindMap = {
        'LINEBELOW': 'borderbottom',
        'LINEABOVE': 'bordertop',
        'LINEBEFORE': 'borderleft',
        'LINEAFTER': 'borderright',
    }

    def getStyleProps(self):
        result = super(LineStyle, self).getStyleProps()

        attrs = self._cachedAttributeValues
        result['kind'] = attrs['kind']
        stylestr = convertLineStyle(attrs)
        if attrs['kind'] in self.kindMap:
            # catering a simple ODT setAttribute loop
            result['cellProps'][self.kindMap[attrs['kind']]] = stylestr
        else:
            # otherwise there will be special processing in
            # BlockTable.getStyleMap
            result['border'] = stylestr
        return result


class BlockTableStyle(directive.RMLDirective):
    signature = rml_stylesheet.IBlockTableStyle

    factories = {
        'blockFont': BlockFont,
        'blockTextColor': BlockTextColor,
        'blockLeading': BlockLeading,
        'blockAlignment': BlockAlignment,
        'blockValign': BlockValign,
        'blockLeftPadding': BlockLeftPadding,
        'blockRightPadding': BlockRightPadding,
        'blockBottomPadding': BlockBottomPadding,
        'blockTopPadding': BlockTopPadding,
        'blockBackground': BlockBackground,
        'lineStyle': LineStyle,
        'blockSpan': BlockSpan,

        # z3c.rml only features, alternating row/col colors,
        # no start/stop attributes
        'blockRowBackground': BlockRowBackground,
        'blockColBackground': BlockColBackground,
    }

    def process(self):
        self.collector = defaultdict(list)

        # Create Style
        manager = attr.getManager(self)
        attrs = dict(self.getAttributeValues())
        self.styleID = attrs.pop('id')
        manager.styles[self.styleID] = self

        self.processSubDirectives()


BULLETS = {
    'bulletchar': u'\u2022',
    'circle': u'\u25cf',
    'square': u'\u25AA',
    'diamond': u'\u2B29',
    'darrowhead': u'\u2304',
    'rarrowhead': u'\u27a4'
}


def registerListStyle(doc, name, rmlStyle, attributes=None, ulol=None):
    """Registers an rmlStyle as ODF styles

    rmlStyles have information both for ordered and unordered lists,
    ODF styles do not, so we need to register two different, but similar lists.
    """
    if ulol is None:
        # Register both the unordered and ordered lists. odf seem to only
        # include the ones actually used anyway.
        registerListStyle(doc, name, rmlStyle, attributes=attributes,
                          ulol='ul')
        registerListStyle(doc, name, rmlStyle, attributes=attributes,
                          ulol='ol')
        return

    name = '%s-%s' % (name, ulol)

    if attributes is None:
        attributes = {}
    start = attributes.get('start', getattr(rmlStyle, 'start', 1))
    if isinstance(start, int):
        bulletType = None
    else:
        bulletType = start

    numType = attributes.get('bulletType',
                             getattr(rmlStyle, 'bulletType', None))
    bulletFormat = attributes.get('bulletFormat',
                                  getattr(rmlStyle, 'bulletFormat', None))
    bulletDedent = attributes.get('bulletDedent',
                                  getattr(rmlStyle, 'bulletDedent', 'auto'))

    if bulletDedent is None or bulletDedent == 'auto':
        bulletDedent = 18

    if isinstance(bulletDedent, six.string_types):
        units = {'in': reportlab.lib.units.inch,
                 'cm': reportlab.lib.units.cm,
                 'mm': reportlab.lib.units.mm,
                 'pt': 1}

        bulletDedent = float(bulletDedent[:-2]) * units[bulletDedent[-2:]]

    odtStyle = odf.text.ListStyle(name=name)

    # Add the level properties:
    for level in range(1, 11):

        # Declare properties of the list style
        listProps = odf.style.ListLevelProperties()
        listProps.setAttribute('listlevelpositionandspacemode',
                               'label-alignment')
        if getattr(rmlStyle, 'bulletFontName', None) is not None:
            odf_font_name = rmlFont2odfFont(rmlStyle.bulletFontName)

            if odf_font_name not in [x.getAttribute('name')
                                     for x in doc.fontfacedecls.childNodes]:
                doc.fontfacedecls.addElement(
                    odf.style.FontFace(
                        name=odf_font_name,
                        fontfamily=odf_font_name))
                listProps.setAttribute('fontname', odf_font_name)

        level_indent = (18 * (level-1)) + bulletDedent
        label_align = odf.style.ListLevelLabelAlignment(
            labelfollowedby="listtab",
            listtabstopposition="%spt" % level_indent,
            textindent="-%spt" % bulletDedent,
            marginleft="%spt" % level_indent)
        listProps.appendChild(label_align)

        # Make the number (ol) style:
        if ulol == 'ol':
            # if numType is just one character (or None)
            # means some sort of number
            if bulletFormat is not None:
                pre, post = bulletFormat.split('%s')
            else:
                pre = post = ''

            if numType and numType.lower() not in '1ai':
                # ODF doesn't support fancy formats like '1st' or 'First'.
                # Make a number format that is empty.
                odtStyle.fancy_numbering = numType
                odtStyle.post = post
                odtStyle.pre = pre
                post = pre = ''
                numType = ''

            lvl_style = odf.text.ListLevelStyleNumber(
                level=level,
                numsuffix=post,
                numprefix=pre,
                numformat=numType,
                startvalue=start,
            )
        else:
            # bullet / ul style
            retrievedBullet = BULLETS.get(bulletType)
            if bulletType and retrievedBullet is None:
                # The bullet is a text, such as "RESOLVED:" etc
                lvl_style = odf.text.ListLevelStyleNumber(
                    level=level,
                    # A bug in the DOCX conversion removes the first character.
                    # A space first in the prefix and a space as suffix
                    # fixes that.
                    numprefix=' ' + bulletType,
                    numsuffix=' ',
                    numformat='')
            else:
                # Make the bullet (ul) style:
                if retrievedBullet is None:
                    retrievedBullet = BULLETS['bulletchar']
                lvl_style = odf.text.ListLevelStyleBullet(
                    bulletchar=retrievedBullet,
                    level=level,
                    bulletrelativesize='75%')

        lvl_style.addElement(listProps)
        odtStyle.addElement(lvl_style)

    pstyle = odf.style.Style(name='P%s' % name,
                             parentstylename='Standard',
                             liststylename=name,
                             family='paragraph'
                             )
    doc.automaticstyles.addElement(pstyle)

    # Add the style to the doc
    doc.automaticstyles.addElement(odtStyle)


class ListStyle(directive.RMLDirective):
    signature = rml_stylesheet.IListStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop('parent', None)
        if parent is not None:
            # Get the style attribs from the parent
            style_attrs = dict(self.getAttributeValues(includeMissing=True))
            pkwargs = {att: getattr(parent, att)
                       for att in style_attrs if
                       hasattr(parent, att)}
            # Override them with selfs.
            pkwargs.update(kwargs)
            # replace
            kwargs = pkwargs

        # Make a new style
        style = reportlab.lib.styles.ListStyle(name=None)
        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style
        registerListStyle(manager.document, kwargs.get('name'), style, kwargs)


class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'spanStyle': SpanStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
    }
