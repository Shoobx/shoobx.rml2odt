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
from docx.enum.text import WD_BREAK
from z3c.rml import directive
from z3c.rml import flowable as rml_flowable
from docx.shared import RGBColor

class Paragraph(directive.RMLDirective):
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
        style = self.element.attrib.get('style', self.defaultStyle)
        paragraph = self.parent.container.add_paragraph(style=style)
        self._handleText(self.element, paragraph)
        return paragraph

class li(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = 'ListBullet'

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, li):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = li.add_run(self._cleanText(element.text.lstrip()))

    def process(self):
        style = self.element.attrib.get('style', self.defaultStyle)
        li = self.parent.container.add_paragraph(style = style)
        self._handleText(self.element, li)
        return li

class num(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = 'ListNumber'

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, num):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = num.add_run(self._cleanText(element.text.lstrip()))

    def process(self):
        style = self.element.attrib.get('style', self.defaultStyle)
        num = self.parent.container.add_paragraph(style = style)
        self._handleText(self.element, num)
        return num

class Heading(directive.RMLDirective):
    #signature = None
    defaultStyle = "Heading"

    def _cleanText(self, text):
        if not text:
            text = ''
        text = re.sub('\n\s+', ' ', text)
        text = re.sub('\s\s\s+', '', text)
        text = re.sub('\t', '', text)
        return text

    def _handleText(self, element, heading):
        # Maybe recursive implementation for nested tags
        if element.text is not None and element.text.strip() != '':
            run = heading.add_run(self._cleanText(element.text.lstrip()))

            ## !! Look at this
        #print(type(element.tag))

    def process(self):
        #import pdb; pdb.set_trace()
        #Takes care of different heading tags
        tagNo = self.element.tag[-1]
        style = self.element.attrib.get('style', self.defaultStyle)+"%s"%tagNo
        self.signature = eval("rml_flowable.IHeading%s"%tagNo)
        # Set signature based on heading tag
        # This makes initial signature declaration obsolete
        heading = self.parent.container.add_paragraph(style=style)
        self._handleText(self.element, heading)
        return heading

class br(directive.RMLDirective):
    signature = rml_flowable.IParagraph
    defaultStyle = None

    def process(self):
        paragraph = self.parent.container.add_paragraph()
        run = paragraph.add_run()
        #run.add_break(WD_BREAK.LINE)
        #br = self.parent.container.add_paragraph(style=style)
        return run

class hr(directive.RMLDirective):
    signature = rml_flowable.IHorizontalRow
    defaultStyle = None

    def _handleText(self, element, hr):
        # Maybe recursive implementation for nested tags
        run = hr.add_run(element)

    def process(self):
        hr = self.parent.container.add_paragraph()
        docx_bar = u'────────────────────────────────────────────────────────────'
        pdf_bar = u'───────────────────────────────────────'
        self._handleText(docx_bar, hr)
        #br = self.parent.container.add_paragraph(style=style)
        return hr

class title(directive.RMLDirective):
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
        # Maybe recursive implementation for nested tags
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
        # Paragraph-Like Flowables
        'para': Paragraph,
        # Text 
        'li': li,
        # Headers
        'h1': Heading,
        'h2': Heading,
        'h3': Heading,
        'h4': Heading, 
        'h5': Heading,
        'h6': Heading,
        'br': br,
        'title': title,
        'num':num,
        'hr':hr,
    }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)

    def process(self):
        self.processSubDirectives()


