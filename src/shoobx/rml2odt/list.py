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
from odf.text  import P, H, A, S, List, ListItem, ListStyle, ListLevelStyleBullet
from odf.text  import ListLevelStyleNumber, ListLevelStyleBullet, Span
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
    createdLiStyles = {}

    def modifyStyle(self):
        if isinstance(self, UnorderedListItem):
            # Retrieve parent list's style
            parentStyleName = ListBase.createdStylesDict[self.parent.styleID]
            parentStyle = ListBase.createdStylesLog.get(parentStyleName, None)
            # Tweak inherited style
            modifiedStyle = parentStyle
            if modifiedStyle is not None:
                bullet = ListLevelStyleBullet(
                    level=str(self.parent.level), 
                    stylename="Standard",
                    bulletchar=UnorderedListItem.bulletDict.get('value', 'disc')
                    )
                modifiedStyle.addElement(bullet)
                ListItem.createdLiStyles[self.styleID] = modifiedStyle(name="Q1")

    def _convertSimpleContent(self):
        # Check whether we need to create a para element.
        # 1. Is there text in the element?
        # 2. Are any of the children valid Flow elements?
        if ((self.element.text is not None and
             not self.element.text.strip()) or
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
        self.item = odf.text.ListItem()
        self.parent.list.addElement(self.item)
        self.contents = self.item
        super(ListItem, self).process()
        # self.modifyStyle()


class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem
    #


class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']
    bulletDict = {
    'disc':u'\u2022',
    'square':u'\u25AA',
    'diamond':u'\u2B29',
    'rarrowhead':u'\u2B9E'
    }
    bulletList = ['disc', 'square', 'diamond', 'rarrowhead']


class createStyle(object):
    # XXX: styleCount starts with 3 so that 1 & 2 can be defaults
    styleCount = 2

    def applyAttributes(self, attributes):
        if self.tag == "ul":
            new_style = ListStyle(name=self.name, consecutivenumbering=False)
            bulletList = UnorderedListItem.bulletList
            # listLevel-1 is used because the numbering of levels begins from 1
            # but the indexing of the bullet list starts at 0
            selectedBullet = bulletList[self.listLevel-1%len(bulletList)]
            # XXX: Perhaps worry about list general bullet specifications
            bullet = ListLevelStyleBullet(
                level=str(self.listLevel), 
                stylename="Standard",
                bulletchar=UnorderedListItem.bulletDict[selectedBullet]
                )
            prop = ListLevelProperties(
                spacebefore=self.spacebefore, 
                # XXX: What does this acc do?
                minlabelwidth="0.25in", 
                fontname=attributes.get('bulletFontName', 'Arial')
                )
            bullet.addElement(prop)
            new_style.addElement(bullet)


        elif self.tag == "ol":
            new_style = ListStyle(name=self.name)
            numstyle = ListLevelStyleNumber(
                level=str(self.listLevel), 
                stylename="Numbering_20_Symbols", 
                numsuffix=".", 
                numformat='1'
                )
            prop = ListLevelProperties(
                spacebefore=self.spacebefore, 
                minlabelwidth="0.25in", 
                fontname=attributes.get('bulletFontName', 'Arial')
                )
            numstyle.addElement(prop)
            new_style.addElement(numstyle)

        return new_style


    def getStyle(self):
        return self.new_style


    def addToDocumentStyles(self, parent):
        while parent.element.tag != 'document':
            parent = parent.parent
        parent.document.automaticstyles.addElement(self.new_style)
        ListBase.createdStylesLog[self.name] = self.new_style


    def __init__(self, tag, listLevel, parent, attributes):
        createStyle.styleCount += 1
        self.name = "Sh%d"%createStyle.styleCount
        # Tag is used later on for list specific processing
        self.tag = tag
        self.attributes = attributes
        # XXX: Correct list level
        self.listLevel  = listLevel
        self.parent = parent
        # May not be necessary unless fundamental override happens
        self.spacebefore = str(0.25*self.listLevel) + "in"
        self.new_style = createStyle.applyAttributes(self, self.attributes)
        self.addToDocumentStyles(self.parent)


class ListBase(flowable.Flowable):
    factories = {'li': ListItem}
    attrMapping = {}
    # Stores list id and maps that to name of created style
    createdStylesDict = {}
    # Stores name of created style and maps that to copy of the style element itself
    createdStylesLog = {}


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


    def createList(self):
        # XXX: Removed id from here
        # Applies style retrieved from createdStylesDict
        styleName = ListBase.createdStylesDict[self.styleID]
        self.list = odf.text.List(
            stylename=styleName
            )
        self.contents.addElement(self.list)


    def determineStyle(self):
        # Checks if the list was supplied an already declared style
        existingStyleName = self.element.attrib.get('style', None)
        # Creates a new style if an exisitng style does not exist
        if existingStyleName == None:
            style = createStyle(self.element.tag, self.level, self.parent, 
                self.element.attrib)
            ListBase.createdStylesDict[self.styleID] = style.name
        else:
            # XXX: Find a way to check if provided styleNames have already been initialized
            ListBase.createdStylesDict[self.styleID] = existingStyleName


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

        # Handles list style creation
        children = self.element.getchildren()
        if len(children)==0: return
        else:
            # Generates a random styleID for each new list
            self.styleID = str(uuid.uuid4())
            self.determineStyle()
            # XXX: Check back on this
            for child in children: self.createList()

        # Add all list items.
        self.processSubDirectives()


class OrderedList(ListBase):
    signature = rml_list.IOrderedList
    flowable.Flow.factories['li'] = OrderedListItem
    factories = {'li': OrderedListItem}


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
