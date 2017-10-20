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
import six
import zope.interface

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
    attrMapping = {'id': 'name'}
    factories = {
        'header': Header,
        'footer': Footer,
    }

    def process(self):
        manager = attr.getManager(self)
        styleName = manager.getNextStyleName('Mpm')

        attrMapping = {'bottomMargin': 'marginbottom',
                       'topMargin': 'margintop',
                       'leftMargin': 'marginleft',
                       'rightMargin': 'marginright',
                       'pagesize': 'pagesize',
                       'showBoundary': 'border',
                       }
        args = dict(self.parent.getAttributeValues(attrMapping=attrMapping))
        allowed = attrMapping.values()
        styleArgs = {}
        for arg in args:
            if arg not in allowed:
                continue
            if arg == 'pagesize':
                styleArgs['pagewidth'] = '%spt' % args[arg][0]
                styleArgs['pageheight'] = '%spt' % args[arg][1]
            elif arg == 'border':
                if args[arg]:
                    styleArgs[arg] = "3pt"
                else:
                    styleArgs[arg] = "0pt"
            else:
                styleArgs[arg] = '%spt' % args[arg]

        pageLayout = odf.style.PageLayout(name=styleName)
        pageLayoutProps = odf.style.PageLayoutProperties(**styleArgs)

        pageLayout.addElement(pageLayoutProps)
        manager.document.automaticstyles.addElement(pageLayout)

        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        self.content = odf.style.MasterPage(name=args['name'],
                                            pagelayoutname=styleName)
        self.parent.parent.document.masterstyles.addElement(self.content)
        self.processSubDirectives()


class Template(directive.RMLDirective):
    signature = rml_template.ITemplate

    factories = {
        'pageTemplate': PageTemplate,
    }

    def process(self):
        self.processSubDirectives()
