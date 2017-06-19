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
"""RML ``document`` element
"""
import zope.interface
from odf.opendocument import OpenDocumentText
from reportlab.lib import styles
from z3c.rml import directive, canvas
from z3c.rml import document as rml_document, interfaces as rml_interfaces

from shoobx.rml2docx import template
from shoobx.rml2docx import stylesheet

# Import modules, so their directives get registered.
from shoobx.rml2docx import list, stylesheet, table


RMLSTYLE_HANDLERS = {
    styles.ParagraphStyle: stylesheet.registerParagraphStyle
}


@zope.interface.implementer(rml_interfaces.IManager)
class Document(directive.RMLDirective):
    signature = rml_document.IDocument

    factories = {
        'story': template.Story,
        'pageTemplate': template.PageTemplate,
        'template': template.Template,
        'pageGraphics': template.PageGraphics,
        'stylesheet': stylesheet.Stylesheet
        }

    def __init__(self, element):
        super(Document, self).__init__(element, None)
        self.names = {}
        self.styles = {}
        self.styleCounters = {}
        self.colors = {}
        self.attributesCache = {}
        self.filename = '<unknown>'
        self.attributesCache = {}

    def getNextSyleName(self, prefix):
        self.styleCounters.setdefault(prefix, 0)
        self.styleCounters[prefix] += 1
        return prefix + str(self.styleCounters[prefix])

    def registerDefaultStyles(self):
        for name, style in stylesheet.SampleStyleSheet.byName.items():
            handler = RMLSTYLE_HANDLERS.get(style.__class__)
            if handler is None:
                continue
            handler(self.document, name, style)

    def process(self, outputFile=None, maxPasses=2):
        """Process document"""
        # Initialize the DOCX Document.
        self.document = OpenDocumentText()

        #self.registerDefaultStyles()

        # Process common sub-directives
        #self.processSubDirectives(select=('docinit', 'stylesheet'))
        #self.processSubDirectives(select=('stylesheet',))

        # Handle Flowable-based documents.
        if self.element.find('template') is not None:
            # Probably wanna add style & template info here
            #self.processSubDirectives(select=('template', 'story', 'pageTemplate', 'pageGraphics'))
            self.processSubDirectives(select=('story',))

        # Save the output.
        self.document.save(outputFile)
