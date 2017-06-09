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
from z3c.rml import directive, interfaces
from z3c.rml import template as rml_template
from z3c.rml import page as rml_page


from shoobx.rml2docx import flowable


class Story(flowable.Flow):
    signature = rml_template.IStory

    @property
    def container(self):
        return self.parent.document

class Frame(directive.RMLDirective):
    signature = rml_template.IFrame

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
        'frame': Frame,
        'pageGraphics': PageGraphics,
        'mergePage': rml_page.MergePageInPageTemplate,
        }

    @property
    def container(self):
        return self.parent.document

class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    factories = {
        'pageTemplate': PageTemplate,
        }


    @property
    def container(self):
        return self.parent.document
