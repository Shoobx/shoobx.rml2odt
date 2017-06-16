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
from docx.enum.dml import MSO_THEME_COLOR_INDEX
from docx.enum.style import WD_STYLE
import docx, lxml
from docx.text.run import Font, Run
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from z3c.rml import directive
from z3c.rml import flowable as rml_flowable
from z3c.rml import template as rml_template

from shoobx.rml2docx.interfaces import IContentContainer

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


class BarCodeFlowable(Flowable):
    signature = rml_flowable.IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}


class Paragraph(Flowable):
    signature = rml_flowable.IParagraph
    defaultStyle = 'Normal'

    @property
    def container(self):
        # Goes up the tree to find the content container in order to
        # append new paragraph
        parent = self.parent
        while not IContentContainer.providedBy(parent):
            parent = parent.parent
        return parent.container

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, paragraph):
        # Maybe recursive implementation for nested tags !!
        if (element.text is not None and element.text.strip() != ''):
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

        if element.tag == 'pageNumber':
            run = paragraph.add_run()
            run.pageNumber = True

        for subElement in element:
            self._handleText(subElement, paragraph)

        if element.tail:
            text = self._cleanText(element.tail)
            run = paragraph.add_run(self._cleanText(element.tail))

    def process(self):
        # Takes care of links
        def add_hyperlink(paragraph, url, text):
            # This gets access to the document.xml.rels file and gets
            # a new relation id value
            part = paragraph.part
            r_id = part.relate_to(
                url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK,
                is_external=True)

            # Create the w:hyperlink tag and add needed values
            hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
            hyperlink.set(docx.oxml.shared.qn('r:id'), r_id, )

            # Create a w:r element
            run = docx.oxml.shared.OxmlElement('w:r')

            # Create a new w:rPr element
            rPr = docx.oxml.shared.OxmlElement('w:rPr')

            # Sets the color
            color = docx.oxml.shared.OxmlElement('w:color')
            color.set(docx.oxml.shared.qn('w:val'), '0000FF')
            rPr.append(color)

            # Underlines the text
            underline = docx.oxml.shared.OxmlElement('w:u')
            underline.set(docx.oxml.shared.qn('w:val'), 'single')
            rPr.append(underline)

            # Join all the xml elements together add add the required
            # text to the w:r element
            run.append(rPr)
            run.text = text
            hyperlink.append(run)
            paragraph._p.append(hyperlink)
            return hyperlink

        # Styles within li tags are given to paras as attributes
        # This retrieves and applies the given style
        style = self.element.attrib.get('style', self.defaultStyle)

        # Append new paragraph.
        paragraph = self.container.add_paragraph(style=style)

        # Checks for link tags and passes element to add_hyperlink function
        if self.parent.element.tag == 'link':
            add_hyperlink(
                paragraph,
                self.parent.element.attrib.get('url', None),
                self.element.text)
            return
        self._handleText(self.element, paragraph)
        return paragraph


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

    def _handleText(self, element, hr):
        run = hr.add_run(element)

    def process(self):
        # Implement other alignment styles? self.element.attrib has values
        hr = self.parent.container.add_paragraph()
        hr_format = hr.paragraph_format
        hr_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        docx_bar = u'─────────────────────────────────────────────────────────'
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
        # Note: Using add_heading instead of add_paragraph. Does this
        # still inherit?
        title = self.parent.container.add_heading(level = 0)
        self._handleText(self.element, title)
        return title


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
