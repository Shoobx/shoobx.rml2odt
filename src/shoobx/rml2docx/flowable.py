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
from docx.enum.text import WD_BREAK
from z3c.rml import directive
from z3c.rml import flowable as rml_flowable

class Paragraph(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = None

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
        style = self.element.attrib.get('style', self.defaultStyle)
        paragraph = self.parent.container.add_paragraph(style=style)
        self._handleText(self.element, paragraph)
        return paragraph

class Title(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = None

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, title):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = title.add_run(self._cleanText(element.text.lstrip()))
            run.bold = True
            run.underline = True

    def process(self):
        style = self.element.attrib.get('style', self.defaultStyle)
        title = self.parent.container.add_paragraph(style=style)
        self._handleText(self.element, title)
        return title

class Header(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = None

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, header):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = header.add_run(self._cleanText(element.text.lstrip()))

        if element.tag[-1] == '1':
            run.bold = True
        elif element.tag[-1] == '2':
            run.italic = True
        elif element.tag[-1] == '3':
            run.underline = True
        elif element.tag[-1] == '4':
            run.bold = True
        elif element.tag[-1] == '5':
            run.italic = True
        elif element.tag[-1] == '6':
            run.underline = True

    def process(self):
        style = self.element.attrib.get('style', self.defaultStyle)
        header = self.parent.container.add_paragraph(style=style)
        self._handleText(self.element, header)
        return header

class Flow(directive.RMLDirective):
    factories = {
        # Paragraph-Like Flowables
        'para': Paragraph,
        # Text which should appear in a title
        'Title': Title,
        # Headers
        'h1': Header,
        'h2': Header,
        'h3': Header,
        'h4': Header, 
        'h5': Header,
        'h6': Header
    }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)

    def process(self):
        self.processSubDirectives()


