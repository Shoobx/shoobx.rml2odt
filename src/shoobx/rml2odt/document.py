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

import odf
from odf.svg import FontFaceUri
from odf.svg import DefinitionSrc
from reportlab.lib import styles
import reportlab
import zope.interface

from odf.opendocument import OpenDocumentText
from odf.style import FontFace
from odf.svg import FontFaceSrc
from reportlab.pdfbase import pdfmetrics, ttfonts, cidfonts
from z3c.rml import attr, directive, canvas
from z3c.rml import document as rml_document, interfaces as rml_interfaces

# Import modules, so their directives get registered.
from shoobx.rml2odt import list, stylesheet, table, template


RMLSTYLE_HANDLERS = {
    styles.ParagraphStyle: stylesheet.registerParagraphStyle,
    styles.ListStyle: stylesheet.registerListStyle,
}


class ColorDefinition(directive.RMLDirective):
    signature = rml_document.IColorDefinition

    def process(self):
        attrs = dict(self.getAttributeValues())
        manager = attr.getManager(self)
        manager.colors[attrs['id']] = attrs['value']


class RegisterTTFont(directive.RMLDirective):
    signature = rml_document.IRegisterTTFont

    def process(self):
        fontName, location = self.getAttributeValues(valuesOnly=True)

        font = FontFace(name=fontName, fontfamily=fontName,
                        fontfamilygeneric='modern', fontpitch='variable')

        source = FontFaceSrc()
        urn = FontFaceUri(href=location, actuate='onRequest', type='simple')
        source.appendChild(urn)
        defSource = DefinitionSrc(href=location, actuate='onRequest')
        font.appendChild(source)
        # font.appendChild(defSource)
        self.parent.parent.document.fontfacedecls.addElement(font)


class DocInit(directive.RMLDirective):
    signature = rml_document.IDocInit
    factories = {
        # 'name': special.Name,
        'color': ColorDefinition,
        # 'registerType1Face': RegisterType1Face,
        # 'registerFont': RegisterFont,
        'registerTTFont': RegisterTTFont,
        # 'registerCidFont': RegisterCidFont,
        # 'registerFontFamily': RegisterFontFamily,
        # 'addMapping': AddMapping,
        # 'logConfig': LogConfig,
        # 'cropMarks': CropMarks,
        # 'startIndex': StartIndex,
        }

    viewerOptions = {option[0].lower()+option[1:]: option for option in
                     ['HideToolbar', 'HideMenubar', 'HideWindowUI',
                      'FitWindow', 'CenterWindow', 'DisplayDocTitle',
                      'NonFullScreenPageMode', 'Direction', 'ViewArea',
                      'ViewClip', 'PrintArea', 'PrintClip', 'PrintScaling']}

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
        'template': template.Template,
        # 'pageGraphics': template.PageGraphics,
        'stylesheet': stylesheet.Stylesheet,
        # 'frame': template.Frame
        }

    def __init__(self, element):
        super(Document, self).__init__(element, None)
        self.names = {}
        self.styles = {}
        self.odtStyles = {}
        self.styleCounters = {}
        self.colors = {}
        self.attributesCache = {}
        self.filename = '<unknown>'
        self.attributesCache = {}

    def getNextStyleName(self, prefix):
        self.styleCounters.setdefault(prefix, 0)
        self.styleCounters[prefix] += 1
        return prefix + str(self.styleCounters[prefix])

    def registerDefaultStyles(self):
        for name, style in stylesheet.SampleStyleSheet.byName.items():
            handler = RMLSTYLE_HANDLERS.get(style.__class__)
            if handler is None:
                continue
            odtStyle = handler(self.document, name, style)
            self.odtStyles[name] = odtStyle

    def process(self, outputFile=None, maxPasses=2):
        """Process document"""
        # Initialize the ODT Document.
        self.document = OpenDocumentText()
        self.registerDefaultStyles()
        # Process common sub-directives
        self.processSubDirectives(select=('docinit',))

        # Handle Flowable-based documents.
        if self.element.find('template') is not None:
            self.processSubDirectives(select=('stylesheet', 'template'))
            self.processSubDirectives(select=('story',))
        # Save the output.
        self.document.save(outputFile)
