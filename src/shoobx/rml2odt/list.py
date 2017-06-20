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
"""``ul``, ``ol``, and ``li`` directives.
"""
import copy
import odf.text
import reportlab.lib.styles
import zope.interface
import zope.schema
import re
import lxml
from z3c.rml import list as rml_list
from z3c.rml import stylesheet  as rml_stylesheet
from z3c.rml import flowable as rml_flowable
from z3c.rml import directive
from z3c.rml import stylesheet

from shoobx.rml2odt import flowable
from shoobx.rml2odt.interfaces import IContentContainer


@zope.interface.implementer(IContentContainer)
class ListItem(flowable.Flow):
    signature = rml_flowable.IParagraph
    styleAttributes = zope.schema.getFieldNames(stylesheet.IMinimalListStyle)

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.
        # 1. Is there text in the element?
        # 2. Are any of the children valid Flow elements?
        if (self.element.text is None or
            not self.element.text.strip() or
            any([sub.tag in flowable.Flow.factories
                 for sub in self.element])):
            return
        # Create a <para> element.
        para = lxml.etree.Element('para')
        # Transfer text.
        para.text = self.element.text
        self.element.text = None
        # Transfer children.
        for sub in tuple(self.element):
            para.append(sub)
        # Add paragraph to list item..
        self.element.append(para)

    def process(self):
        self._convertSimpleContent()
        self.item = odf.text.ListItem()
        self.parent.list.addElement(self.item)
        self.contents = self.item
        super(ListItem, self).process()


class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem
    defaultStyle = "ListNumber"


class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']
    defaultStyle = "ListBullet"


class ListBase(flowable.Flowable):
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
        # Create the list element.
        self.list = odf.text.List()
        self.contents.addElement(self.list)
        # Add all list items.
        self.processSubDirectives()


class OrderedList(ListBase):
    signature = rml_list.IOrderedList
    flowable.Flow.factories['li'] = OrderedListItem
    factories = {'li': OrderedListItem}
    styleAttributes = ListBase.styleAttributes + ['bulletType']


class UnorderedList(ListBase):
    signature = rml_list.IUnorderedList
    flowable.Flow.factories['li'] = UnorderedListItem
    attrMapping = {'value': 'start'}
    factories = {'li': UnorderedListItem}

    def getAttributeValues(self, *args, **kw):
        res = super(UnorderedList, self).getAttributeValues(*args, **kw)
        res.append(('bulletType', 'bullet'))
        return res


flowable.Flow.factories['ol'] = OrderedList
flowable.Flow.factories['ul'] = UnorderedList
