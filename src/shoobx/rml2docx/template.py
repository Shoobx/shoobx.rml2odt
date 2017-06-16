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
from shoobx.rml2docx import flowable
from shoobx.rml2docx.directive import NotImplementedDirective
from shoobx.rml2docx.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class Story(flowable.Flow):
    signature = rml_template.IStory

    @property
    def container(self):
        return self.parent.document

@zope.interface.implementer(interfaces.ICanvasManager)
class PageGraphics(directive.RMLDirective):
    signature = rml_template.IPageGraphics

    @property
    def container(self):
        return self.parent.document


class PageTemplate(directive.RMLDirective):
    signature = rml_template.IPageTemplate
    attrMapping = {'autoNextTemplate': 'autoNextPageTemplate'}
    factories = {
        'pageGraphics': NotImplementedDirective,
        'mergePage': NotImplementedDirective,
        'mergePage': NotImplementedDirective
        }


class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    factories = {
        'pageTemplate': PageTemplate,
        }

    @property
    def container(self):
        return self.parent.document



    def process(self):
        args = self.getAttributeValues()
        # pdb.set_trace()
        args += self.parent.getAttributeValues(
            select=('debug', 'compression', 'invariant'),
            attrMapping={'debug': '_debug', 'compression': 'pageCompression'})
        # args += (('cropMarks',  self.parent.cropMarks),)
        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
