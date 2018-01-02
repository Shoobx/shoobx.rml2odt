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

    def _getParaStyle(self):
        # Any childnodes that are paragraphs must have a special style
        # for indentation purposes.
        node = top = self

        while node.parent is not None:
            node = node.parent
            if isinstance(node, ListBase):
                top = node

        top_style = dict(top.getAttributeValues(
            select=['style'],
            attrMapping=top.attrMapping))
        if 'style' in top_style:
            top_style = top_style['style'].name
        else:
            top_style = 'Default'

        if isinstance(top, OrderedList):
            top_style += '-ol'
        else:
            top_style += '-ul'
        return 'P%s' % top_style

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.

        # Any paragraphs should specifically have the lists paragraph style:
        para_style = self._getParaStyle()
        for sub in self.element:
            if sub.tag == 'para':
                sub.attrib['style'] = para_style

        # If there is anything flowable here, we are done.
        if any([sub.tag in flowable.Flow.factories
                for sub in self.element]):
            return

        if (self.element.text is not None and
           not self.element.text.strip(' \t\r\n')):
            return

        # The tag has text in it, create a <para> element.
        para = self.element.makeelement('para', style=para_style)
        # Transfer text.
        para.text = self.element.text
        self.element.text = None
        # Transfer children.
        for sub in tuple(self.element):
            para.append(sub)
        # Add paragraph to list item.
        self.element.append(para)

    def process(self):
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

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)

    def getRootStyle(self):
        parent = self
        root = None
        while True:
            parent = parent.parent
            if isinstance(parent, ListItem):
                continue
            if isinstance(parent, ListBase):
                root = parent
            else:
                break

        manager = attr.getManager(self)
        for style in manager.document.automaticstyles.childNodes:
            if style.getAttribute('name') == root.stylename:
                return style

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

        manager = attr.getManager(self)
        style_attr = dict(self.getAttributeValues(
            select=['style'], attrMapping=self.attrMapping))

        if style_attr:
            style = style_attr['style']
            newstylename = manager.getNextStyleName(style.name)
            newstyle = copy.deepcopy(manager.styles[style.name])
            newstyle.name = newstylename
        else:
            newstylename = manager.getNextStyleName('Default')
            newstyle = None

        attrs = dict(self.getAttributeValues(
            select=self.styleAttributes, attrMapping=self.attrMapping))

        # Always make a special style for each root level list, or numbering
        # is messed up when you convert to docx.
        if self.level == 1:
            # Register style
            stylesheet.registerListStyle(manager.document, newstylename,
                                         newstyle, attrs)
            if isinstance(self, OrderedList):
                newstylename = newstylename + '-ol'
            else:
                newstylename = newstylename + '-ul'
            self.stylename = newstylename

            self.item = odf.text.List(stylename=newstylename)
        else:
            self.item = odf.text.List()

            if newstyle is not None:
                # A non-top level list with a style name.
                # Attempt to copy that styles list styling over to the current
                # level.

                # We only care about these right now:
                newattrs = {'bulletType': newstyle.bulletType,
                            'bulletFormat': newstyle.bulletFormat,
                            }
                # Get any local overrides
                newattrs.update(attrs)
                # OK, we have the new attrs
                attrs = newattrs

            if attrs:
                # We must now find the correct level style, and modify it.
                style = self.getRootStyle()
                for levelstyle in style.childNodes:
                    if not levelstyle.tagName.startswith('text:list-level-style'):
                        # We only care about levels now
                        continue
                    if int(levelstyle.getAttribute('level')) != self.level:
                        continue

                    # Modify this level
                    if levelstyle.tagName == 'text:list-level-style-number':
                        # Ordered list

                        if 'bulletType' in attrs:
                            bulletType = attrs['bulletType']
                            if bulletType.lower() not in '1ai':
                                # ODF doesn't support fancy formats like
                                # '1st' or 'First'.
                                bulletType = '1'

                            levelstyle.setAttribute('numformat', bulletType)

                        if 'bulletFormat' in attrs:
                            bulletFormat = attrs['bulletFormat']
                            pre, post = bulletFormat.split('%s')
                            levelstyle.setAttribute('numprefix', pre)
                            levelstyle.setAttribute('numsuffix', post)

                    if levelstyle.tagName == 'text:list-level-style-bullet':
                        # Unordered list
                        if 'bulletType' in attrs:
                            bulletType = attrs['bulletType']
                            bulletChar = stylesheet.BULLETS[bulletType]
                            levelstyle.setAttribute('bulletchar', bulletChar)

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
