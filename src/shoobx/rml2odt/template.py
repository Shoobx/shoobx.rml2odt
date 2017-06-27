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
"""Style Related Element Processing
"""
import six
import zope.interface

from reportlab import platypus
from z3c.rml import directive, attr, interfaces, occurence
from z3c.rml import template as rml_template
from shoobx.rml2odt import flowable
from shoobx.rml2odt.directive import NotImplementedDirective
from shoobx.rml2odt.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class Story(flowable.Flow):
    signature = rml_template.IStory

    @property
    def contents(self):
        return self.parent.document.text


@zope.interface.implementer(interfaces.ICanvasManager)
class PageGraphics(directive.RMLDirective):
    signature = rml_template.IPageGraphics


class PageTemplate(directive.RMLDirective):
    signature = rml_template.IPageTemplate
    attrMapping = {'autoNextTemplate': 'autoNextPageTemplate'}
    factories = {
        'pageGraphics': PageGraphics,
        }

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        pagesize = args.pop('pagesize', None)

        self.frames = []
        self.pt = platypus.PageTemplate(**args)

        self.processSubDirectives()
        self.pt.frames = self.frames

        if pagesize:
            self.pt.pagesize = pagesize

        self.parent.parent.doc.addPageTemplates(self.pt)


class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    factories = {
        'pageTemplate': PageTemplate,
    }

    def process(self):
        args = self.getAttributeValues()
        args += self.parent.getAttributeValues(
            select=('debug', 'compression', 'invariant'),
            attrMapping={'debug': '_debug', 'compression': 'pageCompression'})
        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
