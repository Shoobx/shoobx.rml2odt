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
import lxml
import re
import reportlab.lib.styles
import uuid
import zope.interface
import zope.schema

from odf.style import FontFace, ListLevelProperties, ParagraphProperties
from odf.style import Style, TextProperties
from odf.text import P, H, A, S, ListItem, ListStyle, ListLevelStyleBullet
from odf.text import List, ListLevelStyleNumber, Span
from reportlab.lib.sequencer import _type2formatter
from shoobx.rml2odt import flowable, stylesheet
from shoobx.rml2odt.interfaces import IContentContainer
from z3c.rml import list as rml_list
from z3c.rml import stylesheet as rml_stylesheet
from z3c.rml import flowable as rml_flowable
from z3c.rml import attr, directive


def fontNameKeyword(fontname):
    """A dict of ListProperties keywords for fontname

    This helper method will create a keyword dict with the fontname
    parameter if a fontname was specified. This is because fontname=None
    will be rendered as fontname="None" in the ODT"""
    if fontname:
        return {'fontname': fontname}
    return {}


@zope.interface.implementer(IContentContainer)
class ListItem(flowable.Flow):
    signature = rml_flowable.IParagraph
    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IMinimalListStyle)
    ListIDTracker = []
    attrMapping = {}

    def modifyStyle(self):
        attrs = self.getAttributeValues(
            select=self.styleAttributes, attrMapping=self.attrMapping)
        if not attrs:
            # No style attributes, do nothing
            return

        # We just want the style name, not the style, and it can be None,
        # so looking directly at the attributes makes sense here:
        parent_style_name = self.parent.element.attrib.get('style', 'Normal')
        manager = attr.getManager(self)
        new_style_name = manager.getNextStyleName(parent_style_name)
        new_style = ListStyle(name=new_style_name)

        numStyle = ListLevelStyleNumber(
            numformat='',
            numsuffix=":",
            level=str(self.parent.level),
        )

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.
        # 1. Is there text in the element?
        # 2. Are any of the children valid Flow elements?
        if (self.element.text is not None and
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
        # Add paragraph to list item.
        self.element.append(para)

    def process(self):
        self.styleID = str(uuid.uuid4())
        self._convertSimpleContent()

        if not self.parent.item.childNodes:
            attrs = {'startvalue': 1}
        else:
            attrs = {}
        self.item = odf.text.ListItem(**attrs)

        self.newStyleName = self.modifyStyle()
        self.parent.item.addElement(self.item)
        self.contents = self.item
        super(ListItem, self).process()


class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem


class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']
    bulletDict = {
        'disc': u'\u25CF',
        'square': u'\u25A0',
        'diamond': u'\u25C6',
        'rarrowhead': u'\u27A4',
    }
    bulletList = ['disc', 'square', 'diamond', 'rarrowhead']


class ListBase(flowable.Flowable):
    factories = {'li': ListItem}
    attrMapping = {}
    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IMinimalListStyle)
    # Stores list id and maps that to name of created style
    createdStylesDict = {}

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)

    def process(self):
        # Keeps track of the root list (in the case of nested lists)
        # Keeps track of the level of each list
        if isinstance(self.parent, ListItem):
            parent_list = self.parent.parent
            self.level = parent_list.level + 1
            self.rootList = parent_list.rootList
        else:
            self.level = 1
            self.rootList = self

        # Always make a special style for each list, or numbering is messed
        # up when you convert to docx.
        manager = attr.getManager(self)
        self.styleID = str(uuid.uuid4())
        attrs = dict(self.getAttributeValues(
            select=['style'], attrMapping=self.attrMapping))
        if attrs:
            style = attrs['style']

            newstylename = manager.getNextStyleName(style.name)
            newstyle = copy.deepcopy(manager.styles[style.name])
            newstyle.name = newstylename

            # Register style
            attrs = dict(self.getAttributeValues(
                select=self.styleAttributes, attrMapping=self.attrMapping))
            stylesheet.registerListStyle(manager.document, newstylename,
                                         newstyle, attrs)
        else:
            newstylename = None
        self.item = odf.text.List(stylename=newstylename)
        self.parent.contents.addElement(self.item)
        # Add all list items.
        self.processSubDirectives()


class OrderedList(ListBase):
    signature = rml_list.IOrderedList
    flowable.Flow.factories['li'] = OrderedListItem
    factories = {'li': OrderedListItem}


class UnorderedList(ListBase):
    signature = rml_list.IUnorderedList
    flowable.Flow.factories['li'] = UnorderedListItem
    factories = {'li': UnorderedListItem}


flowable.Flow.factories['ol'] = OrderedList
flowable.Flow.factories['ul'] = UnorderedList
