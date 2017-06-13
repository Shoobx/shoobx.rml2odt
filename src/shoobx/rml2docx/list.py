##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
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
"""``ul``, ``ol``, and ``li`` directives.
"""
import copy
import reportlab.lib.styles
import zope.schema
import re
#from lxml import etree

from z3c.rml import list as rml_list
from z3c.rml import stylesheet  as rml_stylesheet
from shoobx.rml2docx import flowable
from z3c.rml import flowable as rml_flowable
from z3c.rml import directive
from z3c.rml import stylesheet

class ListItem(flowable.Flow):
    signature = rml_flowable.IParagraph
    defaultStyle = 'ListNumber'
    styleAttributes = zope.schema.getFieldNames(stylesheet.IMinimalListStyle)

    def process(self):
        self.processSubDirectives()
        children = self.element.getchildren()
        # Takes care of case where li object does not have <para> tag 
        # if len(children) == 0:
        #     newPara = lxml.etree.Element('para')
        #     newPara.text = self.element.text
        #     self.element.text = None
        #     for subElement in tuple(self.element): newPara.append(subElement)
        #     self.element.append(newPara)
        style = self.element.attrib.get('style', self.defaultStyle)
        # '.parent' is used twice because of the nested <li>
        paragraph = self.parent.parent.container.add_paragraph(style=style)
        # Keeps checking until text is found
        element = self.element
        text = element.text
        while text == None:
            element = element.getchildren()[0]
            text = element.text
        run = paragraph.add_run(text)

class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem

class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']

class ListBase(directive.RMLDirective):
    klass = rml_flowable.reportlab.platypus.ListFlowable
    factories = {'li': ListItem}
    attrMapping = {}
    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IBaseListStyle)

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)

    def processStyle(self, style):
        attrs = self.getAttributeValues(
            select=self.styleAttributes, attrMapping=self.attrMapping)
        if attrs:
            style = copy.deepcopy(style)
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        self.processSubDirectives()
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))

class OrderedList(ListBase):
    signature = rml_list.IOrderedList
    flowable.Flow.factories['li'] = OrderedListItem
    factories = {'li': OrderedListItem}
    styleAttributes = ListBase.styleAttributes + ['bulletType']

class UnorderedList(ListBase):
    signature = rml_list.IUnorderedList
    attrMapping = {'value': 'start'}
    factories = {'li': UnorderedListItem}

    def getAttributeValues(self, *args, **kw):
        res = super(UnorderedList, self).getAttributeValues(*args, **kw)
        res.append(('bulletType', 'bullet'))
        return res

flowable.Flow.factories['ol'] = OrderedList
flowable.Flow.factories['ul'] = UnorderedList

