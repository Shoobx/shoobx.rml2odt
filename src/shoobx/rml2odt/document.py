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
import reportlab
from odf.opendocument import OpenDocumentText
from reportlab.lib import styles
from z3c.rml import directive, canvas
from z3c.rml import document as rml_document, interfaces as rml_interfaces


from shoobx.rml2odt import template
from shoobx.rml2odt import stylesheet

# Import modules, so their directives get registered.
from shoobx.rml2odt import list, stylesheet, table


RMLSTYLE_HANDLERS = {
    styles.ParagraphStyle: stylesheet.registerParagraphStyle
}

class ColorDefinition(directive.RMLDirective):
    signature = rml_document.IColorDefinition

    def process(self):
        kwargs = dict(self.getAttributeValues())
        id = kwargs.pop('id')
        colorVal = self.element.attrib.get('value')
        if colorVal.startswith('#'):
            setattr(reportlab.lib.colors, id, reportlab.lib.colors.HexColor(colorVal))
        

class DocInit(directive.RMLDirective):
    signature = rml_document.IDocInit
    factories = {
        # 'name': special.Name,
        'color': ColorDefinition,
        # 'registerType1Face': RegisterType1Face,
        # 'registerFont': RegisterFont,
        # 'registerTTFont': RegisterTTFont,
        # 'registerCidFont': RegisterCidFont,
        # 'registerFontFamily': RegisterFontFamily,
        # 'addMapping': AddMapping,
        # 'logConfig': LogConfig,
        # 'cropMarks': CropMarks,
        # 'startIndex': StartIndex,
        }

    viewerOptions = dict(
        (option[0].lower()+option[1:], option)
        for option in ['HideToolbar', 'HideMenubar', 'HideWindowUI', 'FitWindow',
                       'CenterWindow', 'DisplayDocTitle',
                       'NonFullScreenPageMode', 'Direction', 'ViewArea',
                       'ViewClip', 'PrintArea', 'PrintClip', 'PrintScaling'])

    def process(self):
        kwargs = dict(self.getAttributeValues())
        self.parent.cropMarks = kwargs.get('useCropMarks', False)
        self.parent.pageMode = kwargs.get('pageMode')
        self.parent.pageLayout = kwargs.get('pageLayout')
        for name in self.viewerOptions:
            setattr(self.parent, name, kwargs.get(name))
        super(DocInit, self).process()



@zope.interface.implementer(rml_interfaces.IManager)
class Document(directive.RMLDirective):
    signature = rml_document.IDocument

    factories = {
        'docinit': DocInit,
        'story': template.Story,
        # 'template': template.Template,
        # 'pageGraphics': template.PageGraphics,
        'stylesheet': stylesheet.Stylesheet,
        # 'frame': template.Frame
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
        # Initialize the ODT Document.
        self.document = OpenDocumentText()
        self.registerDefaultStyles()
        # Process common sub-directives
        self.processSubDirectives(select=('docinit'))

        # Handle Flowable-based documents.
        if self.element.find('template') is not None:
            self.processSubDirectives(select=('stylesheet'))
            self.processSubDirectives(select=('story'))


        # Save the output.
        self.document.save(outputFile)
