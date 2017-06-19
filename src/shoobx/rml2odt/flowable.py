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
import odf.style
import odf.text
import re
import zope.interface
from z3c.rml import directive, occurence
from z3c.rml import flowable as rml_flowable
from z3c.rml import template as rml_template

# from z3c.rml flowable.py file
from z3c.rml import attr, directive, interfaces, platypus
try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import types
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.createBarcodeDrawing = None


from shoobx.rml2odt.interfaces import IContentContainer


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
    # outpur snippets.
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
    def container(self):
        # Goes up the tree to find the content container in order to
        # append new paragraph
        parent = self.parent
        while not IContentContainer.providedBy(parent):
            parent = parent.parent
        return parent.container

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))


class Spacer(Flowable):
    signature = rml_flowable.ISpacer
    klass = reportlab.platypus.Spacer
    attrMapping = {'length': 'height'}


class Illustration(Flowable):
    signature = rml_flowable.IIllustration
    klass = platypus.Illustration

    def process(self):
        args = dict(self.getAttributeValues())


class BarCodeFlowable(Flowable):
    signature = rml_flowable.IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}


class SubParagraphDirective(directive.RMLDirective):

    @lazy.lazy
    def paragraph(self):
        para = self.parent
        while not IParagraph.providedBy(para):
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


class IItalic(IComplexSubParagraphDirective):
    """Renders the text inside as italic."""

class Italic(ComplexSubParagraphDirective):
    signature = IItalic

    def preProcess(self):
        self.setStyle('italic', True)


class IBold(IComplexSubParagraphDirective):
    """Renders the text inside as bold."""

class Bold(ComplexSubParagraphDirective):
    signature = IBold

    def preProcess(self):
        self.setStyle('bold', True)


class IUnderline(IComplexSubParagraphDirective):
    """Renders the text inside as underline."""

class Underline(ComplexSubParagraphDirective):
    signature = IUnderline

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


class IBreak(interfaces.IRMLDirectiveSignature):
    """Adds a break in the paragraph.
    """

class Break(SubParagraphDirective):
    signature = IBreak

    def process(self):
        span = self.paragraph.odtParagraph.addElement(odf.text.LineBreak())

        if self.element.tail:
            self.paragraph.addSpan(self.element.tail)


class IPageNumber(interfaces.IRMLDirectiveSignature):
    """Adds a break in the paragraph.
    """

class PageNumber(SubParagraphDirective):
    signature = IPageNumber

    def process(self):
        span = self.paragraph.addSpan()
        # XXX: TO BE DONE!!!

        if self.element.tail:
            self.paragraph.addSpan(self.element.tail)


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
    'pageNumber': PageNumber,
    # Unsupported tags:
    # 'greek': Greek,
}

IComplexSubParagraphDirective.setTaggedValue(
    'directives',
    (occurence.ZeroOrMore('i', IItalic),
     occurence.ZeroOrMore('b', IBold),
     occurence.ZeroOrMore('u', IUnderline),
     occurence.ZeroOrMore('strike', IStrike),
     occurence.ZeroOrMore('strong', IBold),
     occurence.ZeroOrMore('font', IFont),
     occurence.ZeroOrMore('super', ISuper),
     occurence.ZeroOrMore('sub', ISub),
     occurence.ZeroOrMore('a', IAnchor),
     occurence.ZeroOrMore('br', IBreak),
    )
)

class IParagraph(zope.interface.Interface):
    pass

@zope.interface.implementer(IParagraph)
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
        self.container.styles.addElement(style)
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

    def process(self):
        # Styles within li tags are given to paras as attributes
        # This retrieves and applies the given style
        #style = self.element.attrib.get('style', self.defaultStyle)

        # Append new paragraph.
        self.odtParagraph = odf.text.P()
        self.container.text.addElement(self.odtParagraph)

        if self.element.text:
            self.addSpan(self.element.text)

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


class Heading2(Paragraph):
    signature = rml_flowable.IHeading2
    defaultStyle = "Heading2"
    overrideStyle = None


class Heading3(Paragraph):
    signature = rml_flowable.IHeading3
    defaultStyle = "Heading3"


class Heading4(Paragraph):
    signature = rml_flowable.IHeading4
    defaultStyle = "Heading4"


class Heading5(Paragraph):
    signature = rml_flowable.IHeading5
    defaultStyle = "Heading5"


class Heading6(Paragraph):
    signature = rml_flowable.IHeading6
    defaultStyle = "Heading6"


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


class HorizontalRow(Flowable):
    signature = rml_flowable.IHorizontalRow
    klass = reportlab.platypus.flowables.HRFlowable
    attrMapping = {'align': 'hAlign'}

    def process(self):
        # Implement other alignment styles? self.element.attrib has values
        hr = odf.text.P(stylename='Horizontal Line')
        self.parent.container.text.addElement(hr)


class Flow(directive.RMLDirective):
    factories = {
        # Generic Flowables
        'spacer': Spacer,
        'illustration': Illustration,
        'barCodeFlowable': BarCodeFlowable,
        'pre': Preformatted,
        #'xpre': XPreformatted,
        # Paragraph-Like Flowables
        'para': Paragraph,
        # Headers
        'h1': Heading1,
        'h2': Heading2,
        'h3': Heading3,
        'h4': Heading4,
        'h5': Heading5,
        'h6': Heading6,
        'title': Title,
        'hr':HorizontalRow,
        'link': Link
    }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)

    def process(self):
        self.processSubDirectives()
