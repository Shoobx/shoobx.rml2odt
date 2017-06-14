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
import re
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
from z3c.rml import directive
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

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        self.parent.flow.append(self.klass(**args))

class Spacer(Flowable):
    signature = rml_flowable.ISpacer
    klass = reportlab.platypus.Spacer
    attrMapping = {'length': 'height'}

# Adjust Process
class Illustration(Flowable):
    signature = rml_flowable.IIllustration
    klass = platypus.Illustration

    def process(self):
        args = dict(self.getAttributeValues())
        self.parent.flow.append(self.klass(self, **args))

class BarCodeFlowable(Flowable):
    signature = rml_flowable.IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}

class Preformatted(Flowable):
    signature = rml_flowable.IPreformatted
    klass = reportlab.platypus.Preformatted

class XPreformatted(Flowable):
    signature = rml_flowable.IXPreformatted
    klass = reportlab.platypus.XPreformatted

class Paragraph(Flowable):
    signature = rml_flowable.IParagraph
    defaultStyle = 'Normal'

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, paragraph):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = paragraph.add_run(self._cleanText(element.text.lstrip()))

        if element.tag == 'i':
            run.italic = True
        elif element.tag == 'b':
            run.bold = True
        elif element.tag == 'u':
            run.underline = True
        elif element.tag == 'br':
            run = paragraph.add_run()
            run.add_break(WD_BREAK.LINE)
            # Do we need to lstrip() the tail in these cases?

        for subElement in element:
            self._handleText(subElement, paragraph)

        if element.tail:
            text = self._cleanText(element.tail)
            run = paragraph.add_run(self._cleanText(element.tail))

    def process(self):
        # Takes care of style for para elements that are nested within li tags
        if str(self.parent.__class__) in ["""<class 'shoobx.rml2docx.list.UnorderedListItem'>""", """<class 'shoobx.rml2docx.list.OrderedListItem'>"""]:
            style = self.defaultStyle
            # style = self.parent.parent.attrib.get('style', self.defaultStyle)
            paragraph = self.parent.parent.parent.container.add_paragraph(style = style)
        else:
            style = self.element.attrib.get('style', self.defaultStyle)
            paragraph = self.parent.container.add_paragraph(style = style)
        self._handleText(self.element, paragraph)
        return paragraph

class Heading1(Paragraph):
    signature = rml_flowable.IHeading1
    defaultStyle = "Heading1"

class Heading2(Paragraph):
    signature = rml_flowable.IHeading2
    defaultStyle = "Heading2"

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

class HorizontalRow(Flowable):
    signature = rml_flowable.IHorizontalRow
    klass = reportlab.platypus.flowables.HRFlowable
    attrMapping = {'align': 'hAlign'}

    def _handleText(self, element, hr):
        run = hr.add_run(element)

    def process(self):
        # Implement other alignment styles? self.element.attrib has values
        hr = self.parent.container.add_paragraph()
        hr_format = hr.paragraph_format
        hr_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        docx_bar = u'──────────────────────────────────────────────────────'
        self._handleText(docx_bar, hr)
        return hr

class Title(directive.RMLDirective):
    signature = rml_flowable.ITitle
    defaultStyle = "Title"

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, title):
        if element.text is not None and element.text.strip() != '':
            run = title.add_run(self._cleanText(element.text.lstrip()))

    def process(self):
        style = self.element.attrib.get('style', self.defaultStyle)
        # Note: Using add_heading instead of add_paragraph. Does this still inherit?
        title = self.parent.container.add_heading(level = 0)
        self._handleText(self.element, title)
        return title

class Flow(directive.RMLDirective):
    factories = {
        # Generic Flowables
        'spacer': Spacer,
        'illustration': Illustration,
        'barCodeFlowable': BarCodeFlowable,
        #'pre': Preformatted,
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
    }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)

    def process(self):
        self.processSubDirectives()

