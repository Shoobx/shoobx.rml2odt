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
import zope.interface
import zope.schema

from lxml import etree
from reportlab.lib import sequencer
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

    def _getStartValue(self, node, default=0):
        for att, value in node.attributes.items():
            if att[1] == 'start-value':
                return value
        return default

    def process(self):
        self._convertSimpleContent()

        parent_style = self.parent.getRootStyle()
        fancy_numbering = getattr(parent_style, 'fancy_numbering', False)
        value = self.element.get('value')
        attrs = {}
        if value and value.isdigit():
            # if there's a forced start number, use it
            # ODT does not really support setting the bullet per paragraph
            # which is also set by the value attribute, that's why we only
            # accept digits here
            index = int(value)
            attrs = {'startvalue': index}
        else:
            count = len(self.parent.item.childNodes)
            if count == 0:
                # Restart the numbering at the start of each list
                # otherwise the default start index is zero, why???
                attrs = {'startvalue': 1}
                index = 1
            else:
                # for fancy_numbering we need to keep track of the index
                # ourselves, including the starting index
                startvalue = self._getStartValue(self.parent.item.childNodes[0])
                index = count + int(startvalue)

        if fancy_numbering:
            # ohwell, let's dig into reportlab internals...
            # we don't want to reimplement all that bullet formatting
            fmter = sequencer._type2formatter[fancy_numbering]
            word = fmter(index)

            # DIY bullet: patch the bullet text into the child para tag's text
            for child in self.element.getchildren():
                if child.tag == 'para':
                    child.text = ''.join((parent_style.pre,
                                          word,
                                          parent_style.post,
                                          '\t',
                                          child.text.lstrip()))
                    break

        self.item = odf.text.ListItem(**attrs)
        self.parent.item.addElement(self.item)
        self.contents = self.item
        self.processSubDirectives()

    def processSubDirectives(self, select=None, ignore=None):
        # Go through all children of the directive and try to process them.
        for element in self.element.getchildren():
            # Ignore all comments
            if isinstance(element, etree._Comment):
                continue

            if element.tag == "blockTable":
                # Make a list instead of a table

                style = self.parent.getRootStyle()
                numlevels = style.getElementsByType(odf.text.ListLevelStyleNumber)
                bulletlevels = style.getElementsByType(odf.text.ListLevelStyleBullet)
                levels = bulletlevels or numlevels

            # Find the current level and get the indent
                for levelstyle in levels:
                    if int(levelstyle.getAttribute('level')) != self.parent.level:
                        continue

                    # This is the level
                    props = levelstyle.getElementsByType(odf.style.ListLevelProperties)
                    if not props:
                        indent = 0
                        break  # No properties in this level!?
                    align = props[0].getElementsByType(odf.style.ListLevelLabelAlignment)
                    if not align:
                        indent = 0
                        break  # No indent in this level!?
                    indent = align[0].getAttribute('textindent')
                    if indent[0] == '-':
                        indent = indent[1:]
                    else:
                        indent = '-' + indent
                    break  # done

                manager = attr.getManager(self)
                newstylename = manager.getNextStyleName('ListTable')
                style_attrs = {'start': ' ', 'bulletDedent': indent}
                stylesheet.registerListStyle(manager.document, newstylename,
                                             None, style_attrs)

                ol = odf.text.List(stylename=newstylename + '-ul')
                self.contents.appendChild(ol)

                # Retrieve the data
                for row in element.getchildren():
                    # Make a list item for each row
                    olItem = odf.text.ListItem()
                    ol.appendChild(olItem)
                    p = odf.text.P()
                    olItem.appendChild(p)

                    for cell in row.getchildren():
                        for text in cell.itertext():
                            p.addText(text.strip())
                        p.addElement(odf.text.Tab())
                continue

            # Raise an error/log any unknown directive.
            if element.tag not in self.factories:
                msg = "Directive %r could not be processed and was " \
                    "ignored. %s" %(element.tag,
                                    directive.getFileInfo(self, element))
                # Record any tags/elements that could not be processed.
                directive.logger.warning(msg)
                if directive.ABORT_ON_INVALID_DIRECTIVE:
                    raise ValueError(msg)
                continue
            if select is not None and element.tag not in select:
                continue
            if ignore is not None and element.tag in ignore:
                continue
            subdirective = self.factories[element.tag](element, self)
            subdirective.process()


class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem


class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']
    # ODT does not really support setting the bullet per paragraph


class ListBase(flowable.Flowable):
    factories = {'li': ListItem}
    attrMapping = {}
    styleAttributes = zope.schema.getFieldNames(rml_stylesheet.IMinimalListStyle)

    def __init__(self, *args, **kw):
        super(ListBase, self).__init__(*args, **kw)

    def getRootStyle(self):
        parent = self
        root = self
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
        if (isinstance(self.parent, ListItem) and
            isinstance(self.parent.parent, type(self))):
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

                    # Modify this level
                    if levelstyle.tagName == 'text:list-level-style-number':

                        # Ordered list
                        if int(levelstyle.getAttribute('level')) != self.level:
                            # Not this level
                            continue

                        if 'bulletType' in attrs:
                            bulletType = attrs['bulletType']
                            levelstyle.setAttribute('numformat', bulletType)

                        if 'bulletFormat' in attrs:
                            bulletFormat = attrs['bulletFormat']
                            pre, post = bulletFormat.split('%s')
                            levelstyle.setAttribute('numprefix', pre)
                            levelstyle.setAttribute('numsuffix', post)

                        break  # done

                    if levelstyle.tagName == 'text:list-level-style-bullet':
                        # Unordered list
                        if int(levelstyle.getAttribute('level')) != self.level:
                            continue

                        if 'bulletType' in attrs:
                            bulletType = attrs['bulletType']
                            bulletChar = stylesheet.BULLETS[bulletType]
                            levelstyle.setAttribute('bulletchar', bulletChar)

                        break  # done

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
