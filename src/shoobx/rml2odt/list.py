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
    ListIDTracker = []
    liStyleCount = 0

    def modifyStyle(self):
        if isinstance(self, UnorderedListItem) and self.element.attrib != {}:
            ListItem.liStyleCount += 1
            # Retrieve parent's list style
            parentStyleName = ListBase.createdStylesDict[self.parent.styleID]
            newStyleName = "Sh_Li%d"%ListItem.liStyleCount

            newStyle = ListStyle(name=newStyleName, consecutivenumbering=False)
            selectedBullet = self.element.attrib.get('value', 'disc')
            bul = ListLevelStyleBullet(
                level=str(self.parent.level), 
                stylename="Standard",
                bulletchar=UnorderedListItem.bulletDict.get(selectedBullet, 
                    UnorderedListItem.bulletDict['disc'])
                )

            prop = ListLevelProperties(
                spacebefore=str(0.25*self.parent.level) + "in", 
                minlabelwidth="0.25in", 
                fontname=self.element.attrib.get('bulletFontName', 'Arial')
                )
            bul.addElement(prop)
            newStyle.addElement(bul)

            # Add to styles repo
            parent = self.parent
            while parent.element.tag != 'document':
                parent = parent.parent
            parent.document.automaticstyles.addElement(newStyle)
            return newStyleName
        else:
            return None


    def createList(self):
        # Attempts to retrieve <li> style name, but sets it to it's parent's 
        # style name if it doesn't have one
        styleName = (self.newStyleName if self.newStyleName!=None 
                    else ListBase.createdStylesDict[self.parent.styleID])

        # Creates a new List ID for every <li> element since each of them 
        # creates a new list
        listID = str(uuid.uuid4())

        # Keeps track of the list ID of every first <li> element
        # for subsequent <li> element lists to continue from
        if self.parent.element.getchildren()[0] == self.element and isinstance(self, OrderedListItem): 
            ListItem.ListIDTracker.append(listID)

        # Creates a new list for each <li> element and continues from the 
        # initial created list by its listID if it's parent is an <ol>
        if isinstance(self, OrderedListItem):
            self.parent.list = odf.text.List(
                id = listID,
                continuelist=ListItem.ListIDTracker[-1],
                stylename=styleName
                )
        else:
        # Creates a new list for each <li> element if it's parent is a <ul>
            self.parent.list = odf.text.List(
                id = listID,
                stylename=styleName
                )

        # Removes the last list ID from the tracker list if the current <li>
        # element is the last element
        if self.parent.element.getchildren()[-1] == self.element and isinstance(self, OrderedListItem):
            del(ListItem.ListIDTracker[-1])

        # Adds list to the document
        self.parent.contents.addElement(self.parent.list)


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
        self.newStyleName = self.modifyStyle()
        self.createList()
        self.parent.list.addElement(self.item)
        self.contents = self.item
        super(ListItem, self).process()
        

class OrderedListItem(ListItem):
    signature = rml_list.IOrderedListItem
    #


class UnorderedListItem(ListItem):
    signature = rml_list.IUnorderedListItem
    styleAttributes = ListItem.styleAttributes + ['value']
    bulletDict = {
    'disc':u'\u25CF',
    'square':u'\u25A0',
    'diamond':u'\u25C6',
    'rarrowhead': u'\u27A4',
    }
    bulletList = ['disc', 'square', 'diamond', 'rarrowhead']


class createStyle(object):
    styleCount = 0

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
                bulletchar=UnorderedListItem.bulletDict.get(selectedBullet, 
                    UnorderedListItem.bulletDict['disc'])
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


    def determineStyle(self):
        # Checks if the list was supplied an already declared style
        existingStyleName = self.element.attrib.get('style', None)
        # Creates a new style if an exisitng style does not exist
        if existingStyleName == None:
            style = createStyle(self.element.tag, self.level, self.parent, 
                self.element.attrib)
            ListBase.createdStylesDict[self.styleID] = style.name
        else:
            # XXX: Find a way to check if provided styleNames have already 
            # been initialized
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

        self.styleID = str(uuid.uuid4())
        self.determineStyle()

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
