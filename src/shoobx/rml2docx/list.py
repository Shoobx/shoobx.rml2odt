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
__docformat__ = "reStructuredText"
import copy
import reportlab.lib.styles
import reportlab.platypus
import zope.schema
from reportlab.platypus import flowables

from z3c.rml import list as rml_list
from z3c.rml import stylesheet  as rml_stylesheet
from z3c.rml import flowable as rml_flowable
from z3c.rml import interfaces as rml_interfaces
from z3c.rml import occurence as rml_occurence
from z3c.rml import directive as rml_directive
from z3c.rml import attr as rml_attr

from shoobx.rml2docx import flowable


class ListItem(rml_flowable.Flow):
    signature = rml_list.IListItem
    klass = reportlab.platypus.ListItem
    attrMapping = {}

    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IMinimalListStyle)

    def processStyle(self, style):
        attrs = self.getAttributeValues(select=self.styleAttributes)
        if attrs or not hasattr(style, 'value'):
            style = copy.deepcopy(style)
            # Sigh, this is needed since unordered list items expect the value.
            style.value = style.start
            for name, value in attrs:
                setattr(style, name, value)
        return style


class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem

class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem

    styleAttributes = ListItem.styleAttributes + ['value']

class ListBase(rml_directive.RMLDirective):
    klass = reportlab.platypus.ListFlowable
    factories = {'li': ListItem}
    attrMapping = {}

    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IBaseListStyle)

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)
        self.flow = []

    def processStyle(self, style):
        attrs = self.getAttributeValues(
            select=self.styleAttributes, attrMapping=self.attrMapping)
        if attrs:
            style = copy.deepcopy(style)
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        args = dict(self.getAttributeValues(
                ignore=self.styleAttributes, attrMapping=self.attrMapping))
        if 'style' not in args:
            args['style'] = reportlab.lib.styles.ListStyle('List')
        args['style'] = self.baseStyle = self.processStyle(args['style'])
        self.processSubDirectives()
        li = self.klass(self.flow, **args)
        self.parent.flow.append(li)

class OrderedList(ListBase):
    signature = rml_list.IOrderedList
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

rml_flowable.Flow.factories['ol'] = OrderedList
rml_flowable.Flow.factories['ul'] = UnorderedList

