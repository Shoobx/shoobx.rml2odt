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
import docx
import zope.interface
from z3c.rml import directive, canvas
from z3c.rml import document as rml_document, interfaces as rml_interfaces

from shoobx.rml2docx import template
<<<<<<< Updated upstream
from shoobx.rml2docx import stylesheet
from shoobx.rml2docx import list
=======
# from shoobx.rml2docx import stylesheet
# from shoobx.rml2docx import list
>>>>>>> Stashed changes


@zope.interface.implementer(rml_interfaces.IManager)
class Document(directive.RMLDirective):
    signature = rml_document.IDocument

    factories = {
        'story': template.Story,
<<<<<<< Updated upstream
        'pageTemplate': template.PageTemplate,
        'template': template.Template,
        'pageGraphics': template.PageGraphics,
        'styleSheet': stylesheet.Stylesheet,
=======
        'template': template.Template,
        'pageTemplate': template.PageTemplate,
        'pagGraphics': template.PageGraphics,
        # 'styleSheet': stylesheet.Stylesheet,
>>>>>>> Stashed changes
        'pageInfo': canvas.PageInfo,
        'pageDrawing': canvas.PageDrawing
        }

    def __init__(self, element):
        super(Document, self).__init__(element, None)
        self.names = {}
        self.styles = {}
        self.colors = {}
        self.filename = '<unknown>'
        self.attributesCache = {}
        self.outputFile = None

    def process(self, outputFile=None, maxPasses=2):
        """Process document"""
        # Initialize the DOCX Document.
        self.document = docx.Document()

        # Process common sub-directives
        #self.processSubDirectives(select=('docinit', 'stylesheet'))

        # Handle Flowable-based documents.
        if self.element.find('template') is not None:
<<<<<<< Updated upstream
            # Probably wanna add style & template info here
            #self.processSubDirectives(select=('template', 'story'))
            self.processSubDirectives(select=('story'))
=======

            self.processSubDirectives(select=('template', 'story'))
            # self.processSubDirectives(select=('story'))

>>>>>>> Stashed changes

        # Save the output.
        self.document.save(outputFile)



class StartIndex(directive.RMLDirective):
    signature = rml_document.IStartIndex

    def process(self):
        kwargs = dict(self.getAttributeValues())
        name = kwargs['name']
        manager = attr.getManager(self)
<<<<<<< Updated upstream
        manager.indexes[name] = tableofcontents.SimpleIndex(**kwargs)
=======
        manager.indexes[name] = tableofcontents.SimpleIndex(**kwargs)
>>>>>>> Stashed changes
