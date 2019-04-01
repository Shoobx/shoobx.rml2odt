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
import odf
import zope.interface

from z3c.rml import directive, attr
from z3c.rml import template as rml_template
from shoobx.rml2odt import flowable
from shoobx.rml2odt.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class Story(flowable.Flow):
    signature = rml_template.IStory

    @property
    def contents(self):
        return self.parent.document.text


@zope.interface.implementer(IContentContainer)
class Header(flowable.Flow):
    signature = rml_template.IPageGraphics
    klass = staticmethod(odf.style.Header)

    def process(self):
        self.contents = self.klass()
        self.parent.content.addElement(self.contents)
        self.processSubDirectives()


class Footer(Header):
    klass = staticmethod(odf.style.Footer)


class PageTemplate(directive.RMLDirective):
    signature = rml_template.IPageTemplate
    factories = {
        'header': Header,
        'footer': Footer,
    }

    def process(self):
        manager = attr.getManager(self)
        styleName = manager.getNextStyleName('Mpm')

        pageLayoutProps = odf.style.PageLayoutProperties(
            **self.parent.styleArgs)
        pageLayout = odf.style.PageLayout(name=styleName)
        pageLayout.addElement(pageLayoutProps)
        manager.document.automaticstyles.addElement(pageLayout)

        args = dict(self.getAttributeValues())
        self.content = odf.style.MasterPage(
            name=args['id'], pagelayoutname=styleName)
        self.parent.parent.document.masterstyles.addElement(self.content)
        self.processSubDirectives()


class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    attrMapping = {'bottomMargin': 'marginbottom',
                   'topMargin': 'margintop',
                   'leftMargin': 'marginleft',
                   'rightMargin': 'marginright',
                   'pagesize': 'pagesize',
                   'showBoundary': 'border',
                   }
    factories = {
        'pageTemplate': PageTemplate,
    }

    def process(self):
        # determine style attributes to be used in PageTemplate
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        allowed = self.attrMapping.values()
        styleArgs = {}
        for argName, argValue in args.items():
            if argName not in allowed:
                continue
            if argName == 'pagesize':
                styleArgs['pagewidth'] = '%spt' % argValue[0]
                styleArgs['pageheight'] = '%spt' % argValue[1]
            elif argName == 'border':
                if argValue:
                    styleArgs[argName] = "3pt"
                else:
                    styleArgs[argName] = "0pt"
            else:
                styleArgs[argName] = '%spt' % argValue
        
        self.styleArgs = styleArgs

        self.processSubDirectives()
