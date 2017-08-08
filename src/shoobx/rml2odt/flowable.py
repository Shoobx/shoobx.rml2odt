#-*- coding: utf-8 -*-
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
"""Flowable Element Processing
"""
import lazy
import lxml
import reportlab.platypus.flowables
import odf.style
import odf.text
import odf.draw
import pyqrcode
import copy
import png
import reportlab.lib.styles
import re
import zope.interface

from reportlab.lib import styles, utils
from z3c.rml import directive, occurence
from z3c.rml import flowable as rml_flowable
from z3c.rml import template as rml_template
from shoobx.rml2odt import stylesheet as rml_stylesheet

# from z3c.rml flowable.py file
from z3c.rml import attr, directive, interfaces, platypus
from shoobx.rml2odt.interfaces import IContentContainer

DEFAULT_IMAGE_UNIT = 'pt'

def pygments2xpre(s, language="python"):
    "Return markup suitable for XPreformatted"
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return s

    from pygments.lexers import get_lexer_by_name

    l = get_lexer_by_name(language)

    h = HtmlFormatter()
    # XXX: Does not work in Python 2, since pygments creates non-unicode
    # output snippets.
    #from io import StringIO
    from six import StringIO
    out = StringIO()
    highlight(s,l,h,out)
    styles = [(cls, style.split(';')[0].split(':')[1].strip())
                for cls, (style, ttype, level) in h.class2style.items()
                if cls and style and style.startswith('color:')]
    from reportlab.lib.pygments2xpre import _2xpre
    return _2xpre(out.getvalue(),styles)


class Flowable(directive.RMLDirective):
    klass=None
    attrMapping = None

    @property
    def contents(self):
        # Goes up the tree to find the content container in order to
        # append new paragraph
        parent = self.parent
        while not IContentContainer.providedBy(parent):
            parent = parent.parent
        return parent.contents

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))


def inputImageIntoDoc(self):
    self.frame = odf.draw.Frame(
        id = self.frameName,
        width = self.frameWidth+DEFAULT_IMAGE_UNIT,
        height = self.frameHeight+DEFAULT_IMAGE_UNIT,
        anchortype= 'as-char',
        )
    self.frame.appendChild(self.image)
    self.contents.addElement(self.frame)

def inputImageIntoCell(self):
    manager = attr.getManager(self)
    paraStyleName = manager.getNextSyleName('ImagePara')
    paraStyle = odf.style.Style(
        family = 'paragraph',
        name = paraStyleName,
        parentstylename = "Standard"
        )
    paraProps = odf.style.ParagraphProperties(
        textalign = self.align,
        justifysingleword = 'false'
        )
    paraStyle.appendChild(paraProps)
    manager.document.automaticstyles.addElement(paraStyle)
    para = odf.text.P(stylename = paraStyleName)

    firstFrameID = manager.getNextSyleName('Frame')
    firstFrameStyleName = manager.getNextSyleName('FrameStyle')
    firstFrameStyle = odf.style.Style(
        family = "graphic",
        name = firstFrameStyleName,
        parentstylename = "Frame"
        )
    graphicsProperties = odf.style.GraphicProperties(
        border="0.06pt",
        padding = "0in",
        shadow = "none",
        verticalpos = "top",
        verticalrel = "baseline"
        )
    firstFrameStyle.appendChild(graphicsProperties)
    manager.document.automaticstyles.addElement(firstFrameStyle)
    firstFrame = odf.draw.Frame(
        name = firstFrameID,
        stylename = firstFrameStyle,
        width = self.frameWidth + DEFAULT_IMAGE_UNIT,
        height = self.frameHeight + DEFAULT_IMAGE_UNIT,
        anchortype = 'as-char',
        zindex = '0'
        )
    textBox = odf.draw.TextBox()
    para2 = odf.text.P()
    secondFrameID = manager.getNextSyleName('InternalFrame')
    secondFrame = odf.draw.Frame(
        id = secondFrameID,
        width = self.frameWidth + DEFAULT_IMAGE_UNIT,
        height = self.frameHeight + DEFAULT_IMAGE_UNIT,
        anchortype = 'char'
    )
    secondFrame.appendChild(self.image)
    para2.appendChild(secondFrame)
    textBox.appendChild(para2)
    firstFrame.appendChild(textBox)
    para.appendChild(firstFrame)
    self.contents.setAttribute('numbercolumnsspanned', '2')
    if isinstance(self, BarCodeFlowable):
        self.contents.setAttribute('numberrowsspanned', '2')
    self.contents.addElement(para)


def getImageDimensions(self):
    attributes = self.element.attrib
    tempFrameWidth = attributes['width'] 
    tempFrameHeight = attributes['height']
    try:
        tempRowHeight = self.parent.parent.element.attrib['rowHeight']
    except:
        tempRowHeight = tempFrameHeight

    regex = '[0-9]+'
    if not tempFrameHeight.isdigit():
        tempFrameHeight = int(re.findall(regex, tempFrameHeight)[0])
    else:
        tempFrameHeight = int(tempFrameHeight)

    if not tempFrameWidth.isdigit():
        tempFrameWidth = int(re.findall(regex, tempFrameWidth)[0])
    else:
        tempFrameWidth = int(tempFrameWidth) 

    if not tempRowHeight.isdigit():
        tempRowHeight = int(re.findall(regex, tempRowHeight)[0])
    else:
        tempRowHeight = int(tempRowHeight)

    if tempRowHeight < 15: tempRowHeight *= 7
    # if tempFrameHeight <50: tempFrameHeight *= 1.2

    # The 0.8 accounts for the padding
    frameHeight = (min(tempFrameHeight, tempRowHeight)) * 0.8
    ratio = float(frameHeight) / tempFrameHeight

    frameWidth = tempFrameWidth * ratio

    finalFrameHeight = str(frameHeight) 
    finalFrameWidth = str(frameWidth) 
    return finalFrameWidth, finalFrameHeight


class Image(Flowable):
    signature = rml_flowable.IImage
    klass = reportlab.platypus.flowables.Image
    attrMapping = {'src': 'filename', 'align': 'hAlign'}


    def process(self):
        attributes = self.element.attrib
        breakPoint = attributes['src'].find(',')
        imageString = attributes['src'][breakPoint + 1:]
        metaData = attributes['src'][:breakPoint]
        fileType = metaData[metaData.find('/') + 1 : metaData.find(';')]
        manager = attr.getManager(self)
        self.align = attributes.get('align', 'left')
        self.frameName = manager.getNextSyleName('ImageFrame')
        self.frameWidth, self.frameHeight = getImageDimensions(self)
        self.binaryImage = odf.office.BinaryData()
        self.binaryImage.addText(imageString)

        self.image = odf.draw.Image(
            type = 'simple',
            show = 'embed',
            actuate = 'onLoad')
        self.image.appendChild(self.binaryImage)

        if self.parent.element.tag != 'td':
            inputImageIntoDoc(self)
        else:
            inputImageIntoCell(self)


class BarCodeFlowable(Flowable):
    signature = rml_flowable.IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}

    def process(self):
        attributes = self.element.attrib
        codeType = attributes.get('code', None)
        url = attributes.get('value', 'https://www.shoobx.com')
        if codeType == 'QR':
            qrCode = pyqrcode.create(url)
            qrAscii = qrCode.png_as_base64_str(scale=5)
            manager = attr.getManager(self)
            self.align = attributes.get('alignment', 'right').lower()
            self.frameName = manager.getNextSyleName('BarcodeFrame')
            self.frameWidth, self.frameHeight = getImageDimensions(self)
            self.binaryImage = odf.office.BinaryData()
            self.binaryImage.addText(qrAscii)
            self.image = odf.draw.Image(
                type = 'simple',
                show = 'embed',
                actuate = 'onLoad')
            self.image.appendChild(self.binaryImage)
            
            if self.parent.element.tag != 'td':
                inputImageIntoDoc(self)
            else:
                inputImageIntoCell(self)
        

class Spacer(Flowable):
    signature = rml_flowable.ISpacer
    klass = reportlab.platypus.Spacer
    attrMapping = {'length': 'height'}

    def process(self):
        manager = attr.getManager(self)
        spacerStyleName = manager.getNextSyleName('Sp')
        spacer = odf.style.Style(name=spacerStyleName, family='paragraph')
        prop = odf.style.ParagraphProperties()
        length = self.element.attrib.get('length', "0.5in")
        unit = length[-2:]
        floatLength = float(length[:-2])/2
        prop.setAttribute("linespacing", str(floatLength)+ unit)
        spacer.addElement(prop)
        self.parent.parent.document.automaticstyles.addElement(spacer)
        self.odtParagraph = odf.text.P()
        self.odtParagraph.setAttribute('stylename', spacerStyleName)
        self.contents.addElement(self.odtParagraph)


class Illustration(Flowable):
    signature = rml_flowable.IIllustration
    klass = platypus.Illustration

    def process(self):
        args = dict(self.getAttributeValues())


class SubParagraphDirective(directive.RMLDirective):

    @lazy.lazy
    def paragraph(self):
        para = self.parent
        while not rml_flowable.IParagraph.providedBy(para):
            para = para.parent
        return para


class IComplexSubParagraphDirective(interfaces.IRMLDirectiveSignature):
    """A sub-paragraph directive that can contian further elements."""


class ComplexSubParagraphDirective(SubParagraphDirective):
    """A sub-paragraph directive that can contian further elements."""
    signature = IComplexSubParagraphDirective
    factories = {}

    def __init__(self, element, parent):
        super(SubParagraphDirective, self).__init__(element, parent)
        self.originalStyles = {}

    def setStyle(self, name, value):
        self.originalStyles[name] = getattr(self.paragraph, name)
        setattr(self.paragraph, name, value)

    def unsetStyles(self):
        for name, value in self.originalStyles.items():
            setattr(self.paragraph, name, value)

    def preProcess(self):
        pass

    def postProcess(self):
        self.unsetStyles()

    def process(self):
        self.preProcess()
        if self.element.text:
            self.paragraph.addSpan(self.element.text)
        self.processSubDirectives()
        self.postProcess()

        if self.element.tail:
            self.paragraph.addSpan(self.element.tail)


class Italic(ComplexSubParagraphDirective):
    signature = rml_flowable.IItalic

    def preProcess(self):
        self.setStyle('italic', True)


class Bold(ComplexSubParagraphDirective):
    signature = rml_flowable.IBold

    def preProcess(self):
        self.setStyle('bold', True)


class Underline(ComplexSubParagraphDirective):
    signature = rml_flowable.IUnderLine

    def preProcess(self):
        self.setStyle('underline', True)


class IStrike(IComplexSubParagraphDirective):
    """Renders the text inside as strike."""


class Strike(ComplexSubParagraphDirective):
    signature = IStrike

    def preProcess(self):
        self.setStyle('strike', True)


class IFont(IComplexSubParagraphDirective):
    """Renders the text inside as strike."""

    face = attr.String(
        title=u'Font face',
        description=u'The name of the font for the cell.',
        required=False)

    size = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text of the cell.',
        required=False)

    color = attr.Color(
        title=u'Font Color',
        description=u'The color in which the text will appear.',
        required=False)


class Font(ComplexSubParagraphDirective):
    signature = IFont

    def preProcess(self):
        data = self.getAttributeValues(
            attrMapping={'face': 'fontName',
                         'size': 'fontSize',
                         'color': 'fontColor'})
        for name, value in data:
            self.setStyle(name, value)


class ISuper(IComplexSubParagraphDirective):
    """Renders the text inside as super.

    Note that a cusotm font size and position is not supported.
    """


class Super(ComplexSubParagraphDirective):
    signature = ISuper

    def preProcess(self):
        self.setStyle('superscript', True)


class ISub(IComplexSubParagraphDirective):
    """Renders the text inside as sub.

    Note that a cusotm font size and position is not supported.
    """


class Sub(ComplexSubParagraphDirective):
    signature = ISub

    def preProcess(self):
        self.setStyle('subscript', True)


class Break(SubParagraphDirective):
    signature = rml_flowable.IBreak

    def process(self):
        span = self.paragraph.odtParagraph.addElement(odf.text.LineBreak())

        if self.element.tail:
            # XXX: ADDED .strip()
            self.paragraph.addSpan(self.element.tail.strip())


class IAnchor(IComplexSubParagraphDirective):
    """Adds an anchor link into the paragraph."""

    url = attr.Text(
        title=u'URL',
        description=u'The URL to link to.',
        required=True)

    backcolor = attr.Color(
        title=u'Background Color',
        description=u'The background color of the link area.',
        required=False)

    color = attr.Color(
        title=u'Font Color',
        description=u'The color in which the text will appear.',
        required=False)

    fontName = attr.String(
        title=u'Font face',
        description=u'The name of the font for the cell.',
        required=False)

    fontSize = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text of the cell.',
        required=False)

    name = attr.Text(
        title=u'Name',
        description=u'The name of the link.',
        required=False)


class Anchor(ComplexSubParagraphDirective):
    signature = IAnchor

    def process(self):
        attrs = dict(self.getAttributeValues())
        anchor = odf.text.A(href=attrs['url'], text=self.element.text)
        if 'name' in attrs:
            anchor.setAttribute('name', attrs['name'])
        self.paragraph.odtParagraph.addElement(anchor)


ComplexSubParagraphDirective.factories = {
    'i': Italic,
    'b': Bold,
    'u': Underline,
    'strike': Strike,
    'strong': Bold,
    'font': Font,
    'super': Super,
    'sub': Sub,
    'a': Anchor,
    'br': Break,
    # 'pageNumber': pageNumber,
    # Unsupported tags:
    # 'greek': Greek,
}

IComplexSubParagraphDirective.setTaggedValue(
    'directives',
    (occurence.ZeroOrMore('i', rml_flowable.IItalic),
     occurence.ZeroOrMore('b', rml_flowable.IBold),
     occurence.ZeroOrMore('u', rml_flowable.IUnderLine),
     occurence.ZeroOrMore('pageNumber', rml_flowable.IPageNumber),
     occurence.ZeroOrMore('strike', IStrike),
     occurence.ZeroOrMore('strong', rml_flowable.IBold),
     occurence.ZeroOrMore('font', IFont),
     occurence.ZeroOrMore('super', ISuper),
     occurence.ZeroOrMore('sub', ISub),
     occurence.ZeroOrMore('a', IAnchor),
     occurence.ZeroOrMore('br', rml_flowable.IBreak),
    )
)

@zope.interface.implementer(rml_flowable.IParagraph)
class Paragraph(Flowable):
    signature = rml_flowable.IParagraph
    defaultStyle = 'Normal'
    factories = {
        'i': Italic,
        'b': Bold,
        'u': Underline,
        'strike': Strike,
        'strong': Bold,
        'font': Font,
        'super': Super,
        'sub': Sub,
        'a': Anchor,
        'br': Break,
        #'pageNumber': PageNumber,
        # Unsupported tags:
        # 'greek': Greek,
    }

    italic = None
    bold = None
    underline = None
    strike = None
    fontName = None
    fontSize  = None
    fontColor = None
    superscript = None
    subscript = None

    overrideStyle = None

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def addSpan(self, text=None):
        if text is not None:
            text = self._cleanText(text)
        span = odf.text.Span(text=text)
        self.odtParagraph.addElement(span)
        manager = attr.getManager(self)
        styleName = manager.getNextSyleName('T')
        style = odf.style.Style(name=styleName, family='text')
        manager.document.styles.addElement(style)
        span.setAttribute('stylename', styleName)
        textProps = odf.style.TextProperties()
        style.addElement(textProps)
        if self.italic:
            textProps.setAttribute('fontstyle', 'italic')
        if self.bold:
            textProps.setAttribute('fontweight', 'bold')
        if self.underline:
            textProps.setAttribute('textunderlinetype', 'single')
        if self.fontName:
            # Make a font declaration, if necessary
            manager.document.fontfacedecls.addElement(
                odf.style.FontFace(
                    name=self.fontName,
                    fontfamily=self.fontName))
            textProps.setAttribute('fontname', self.fontName)
        if self.fontSize:
            textProps.setAttribute('fontsize', self.fontSize)
        if self.strike:
            textProps.setAttribute('textlinethroughstyle', 'solid')
            textProps.setAttribute('textlinethroughtype', 'single')
        if self.fontColor is not None:
            textProps.setAttribute('color', '#'+self.fontColor.hexval()[2:])
        if self.superscript is not None:
            textProps.setAttribute('textposition', 'super 58%')
        if self.subscript is not None:
            textProps.setAttribute('textposition', 'sub 58%')
        return span


    def determineStyle(self):
        try: 
            styleName = self.element.attrib.pop('style')
            if len(self.element.attrib) > 0:
                manager = attr.getManager(self)
                if styleName[-1].isdigit():
                    newStyleName = manager.getNextSyleName(styleName+'.')
                else:
                    newStyleName = manager.getNextSyleName(styleName)

                style = manager.document.getStyleByName(unicode(styleName))
                newStyle = copy.deepcopy(style)
                newStyle.setAttribute('name', newStyleName)
                newStyle.setAttribute('displayname', newStyleName)

                mapper = {'alignment':'textalign'}

                for key in self.element.attrib:
                    value = self.element.attrib[key]

                    try:
                        newStyle.childNodes[0].setAttribute(mapper[key], value)
                    except:
                        try:
                            newStyle.childNodes[1].setAttribute(mapper[key], value)
                        except:
                            continue
                manager.document.automaticstyles.addElement(newStyle)
                return newStyleName
            else:
                self.element.attrib['style'] = styleName
                return styleName
        except:
            return self.defaultStyle


    def process(self):
        self.odtParagraph = odf.text.P()
        # 
        styleName = self.determineStyle()

        self.odtParagraph.setAttribute('stylename', styleName)

        # Append new paragraph.
        self.contents.addElement(self.odtParagraph)

        if self.element.text:
            self.addSpan(self.element.text)

        for child in self.element.getchildren():
            if child.tag == 'span':
                regex = '[a-zA-Z0-9_]{7}-[a-zA-Z0-9_]{3}'
                if re.findall(regex, child.text):
                    self.contents.setAttribute('numbercolumnsspanned', '2')
                self.addSpan(child.text)

        self.processSubDirectives()


class Preformatted(Paragraph):
    signature = rml_flowable.IPreformatted
    klass = reportlab.platypus.Preformatted


class XPreformatted(Paragraph):
    signature = rml_flowable.IXPreformatted
    klass = reportlab.platypus.XPreformatted


class Heading1(Paragraph):
    signature = rml_flowable.IHeading1
    defaultStyle = "Heading1"
    overrideStyle = None


class Heading2(Paragraph):
    signature = rml_flowable.IHeading2
    defaultStyle = "Heading2"
    overrideStyle = None


class Heading3(Paragraph):
    signature = rml_flowable.IHeading3
    defaultStyle = "Heading3"
    overrideStyle = None


class Heading4(Paragraph):
    signature = rml_flowable.IHeading4
    defaultStyle = "Heading4"
    overrideStyle = None


class Heading5(Paragraph):
    signature = rml_flowable.IHeading5
    defaultStyle = "Heading5"
    overrideStyle = None


class Heading6(Paragraph):
    signature = rml_flowable.IHeading6
    defaultStyle = "Heading6"
    overrideStyle = None


class Title(Paragraph):
    signature = rml_flowable.ITitle
    defaultStyle = "Title"


class Link(Flowable):
    signature = rml_flowable.ILink
    attrMapping = {'destination': 'destinationname',
                   'boxStrokeWidth': 'thickness',
                   'boxStrokeDashArray': 'dashArray',
                   'boxStrokeColor': 'color'}
    defaultStyle = "Normal"

    def process(self):
        # Takes care of case where li object does not have <para> tag
        children = self.element.getchildren()
        if len(children) == 0 or children[0].tag != 'para':
            newPara = lxml.etree.Element('para')
            newPara.text = self.element.text
            self.element.text = None
            for subElement in tuple(self.element): newPara.append(subElement)
            self.element.append(newPara)
        flow = Flow(self.element, self.parent)
        flow.process()

class pageNumber(Flowable):
    signature = rml_flowable.IPageNumber

    def process(self):
        manager = attr.getManager(self)
        pageNumberStyleName = manager.getNextSyleName("PageNumber")
        pageNumberStyle = odf.style.Style(
            name=pageNumberStyleName,
            family='paragraph',
            parentstylename='Footer')
        prop = odf.style.ParagraphProperties()
        prop.setAttribute('textalign', 'center')
        pageNumberStyle.addElement(prop)
        manager.document.automaticstyles.addElement(pageNumberStyle)
        self.para = odf.text.P()
        self.para.addText("Page ")
        self.para.appendChild(odf.text.PageNumber())
        self.para.setAttribute('stylename', pageNumberStyleName)
        self.contents.addElement(self.para)


# class pageNumber(Flowable):
#     signature = rml_flowable.IPageNumber

#     def process(self):
#         self.para = odf.text.P()
#         self.para.addText("Page ")
#         self.para.appendChild(odf.text.PageNumber())
#         self.contents.addElement(self.para)


class nextPage(Flowable):
    signature = rml_flowable.INextPage
    klass = reportlab.platypus.PageBreak
    
    def process(self):
        manager = attr.getManager(self)
        pageBreakStyleName = manager.getNextSyleName("PageBreak")
        pageBreakStyle = odf.style.Style(
            name=pageBreakStyleName, 
            family='paragraph',
            parentstylename='Footer')
        prop = odf.style.ParagraphProperties()
        prop.setAttribute('breakbefore', 'page')
        pageBreakStyle.addElement(prop)
        manager.document.automaticstyles.addElement(pageBreakStyle)
        self.para = odf.text.P()
        self.para.setAttribute('stylename', pageBreakStyleName)
        self.contents.addElement(self.para)


class ConditionalPageBreak(Flowable):
    signature = rml_flowable.IConditionalPageBreak
    klass = reportlab.platypus.CondPageBreak



class HorizontalRow(Flowable):
    signature = rml_flowable.IHorizontalRow
    klass = reportlab.platypus.flowables.HRFlowable
    attrMapping = {'align': 'hAlign'}

    def process(self):
        # Implement other alignment styles? self.element.attrib has values
        hr = odf.text.P(stylename='Horizontal Line')
        self.parent.contents.addElement(hr)


class Flow(directive.RMLDirective):
    factories = {
        # Generic Flowables
        'pre': Preformatted,

        # Paragraph-Like Flowables
        'para': Paragraph,
        'h1': Heading1,
        'h2': Heading2,
        'h3': Heading3,
        'h4': Heading4,
        'h5': Heading5,
        'h6': Heading6,
        'title': Title,
        'hr':HorizontalRow,
        'link': Link,

        #Page-Level Flowables
        'nextPage': nextPage,
        'pageNumber': pageNumber,
        'spacer': Spacer,
        # 'condPageBreak': ConditionalPageBreak

        # Graphic flowables
        'illustration': Illustration,
        'barCodeFlowable': BarCodeFlowable,
        'img': Image
    }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)

    def process(self):
        if self.element.tag == 'story':
            self.parent.document.body.childNodes[0].setAttribute('usesoftpagebreaks', 'true')
        self.processSubDirectives()
