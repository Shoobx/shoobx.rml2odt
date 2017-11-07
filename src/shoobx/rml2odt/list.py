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
from odf.text import List, ListLevelStyleNumber, ListLevelStyleBullet, Span
from shoobx.rml2odt import flowable
from shoobx.rml2odt.interfaces import IContentContainer
from z3c.rml import list as rml_list
from z3c.rml import stylesheet as rml_stylesheet
from z3c.rml import flowable as rml_flowable
from z3c.rml import attr, directive
from z3c.rml import stylesheet


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
    styleAttributes = zope.schema.getFieldNames(stylesheet.IMinimalListStyle)
    ListIDTracker = []
    attrMapping = {}

    def modifyStyle(self):
        # Here, instead of using the parent style, it creates one style
        # per list item. No idea why. Is it even needed? /regebro
        attrs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        if not attrs:
            # No attributes, do nothing
            return

        if isinstance(self, OrderedListItem):
            # We just want the style name, not the style, and it can be None,
            # so looking directly at the attributes makes sense here:
            parent_style = self.parent.element.attrib.get('style')
            # Ugh, it's hardcoded on the style name. That may be the only way,
            # but it's still not nice.
            if parent_style == 'Articles':
                units_ordinal = ['zeroth', 'first', 'second', 'third',
                                 'fourth', 'fifth', 'sixth', 'seventh',
                                 'eighth', 'ninth', 'tenth', 'eleventh',
                                 'twelfth', 'thirteenth', 'fourteenth',
                                 'fifteenth', 'sixteenth', 'seventeenth',
                                 'eighteenth', 'nineteenth']
                manager = attr.getManager(self)
                newStyleName = manager.getNextStyleName('Articles')
                regex = '[0-9]+'
                index = int(re.findall(regex, newStyleName)[0])
                newStyle = ListStyle(name=newStyleName)

                numStyle = ListLevelStyleNumber(
                    stylename="Numbering_20_Symbols",
                    numprefix=units_ordinal[index].upper(),
                    numformat='',
                    numsuffix=":",
                    level=str(self.parent.level),
                )
                prop = ListLevelProperties(
                    minlabelwidth="1in",
                    **fontNameKeyword(attrs.get('bulletFontName'))
                )
                numStyle.addElement(prop)
                newStyle.addElement(numStyle)
                manager.document.automaticstyles.addElement(newStyle)
                return newStyleName

            elif parent_style == 'TableList':
                manager = attr.getManager(self)
                newStyleName = manager.getNextStyleName('TableList')
                newStyle = ListStyle(name=newStyleName)
                numStyle = ListLevelStyleNumber(
                    stylename="Numbering_20_Symbols",
                    numprefix=attrs.get('bulletText', 'None').upper(),
                    numformat='',
                    numsuffix="",
                    level=str(self.parent.level),
                )
                prop = ListLevelProperties(
                    spacebefore="1.5in",
                    minlabelwidth="2in",
                    **fontNameKeyword(attrs.get('bulletFontName'))
                )
                numStyle.addElement(prop)
                newStyle.addElement(numStyle)
                manager.document.automaticstyles.addElement(newStyle)
                return newStyleName
            else:
                # We just want the style name, not the style, and it can be
                # None, so looking directly at the attributes makes sense here:
                return parent_style

    def createList(self):
        # Attempts to retrieve <li> style name, but sets it to it's parent's
        # style name if it doesn't have one
        styleName = (self.newStyleName if self.newStyleName is not None
                     else ListBase.createdStylesDict[self.parent.styleID])

        # Creates a new List ID for every <li> element since each of them
        # creates a new list
        listID = str(uuid.uuid4())

        # Keeps track of the list ID of every first <li> element
        # for subsequent <li> element lists to continue from
        if (self.parent.element.getchildren()[0] == self.element and
           isinstance(self, OrderedListItem)):
            ListItem.ListIDTracker.append(listID)

        # Creates a new list for each <li> element and continues from the
        # initial created list by its listID if it's parent is an <ol>
        if isinstance(self, OrderedListItem):
            self.parent.list = odf.text.List(
                id=listID,
                continuelist=ListItem.ListIDTracker[-1],
                stylename=styleName
                )
        else:
            # Creates a new list for each <li> element if it's parent is a <ul>
            self.parent.list = odf.text.List(
                id=listID,
                stylename=styleName
                )

        # Removes the last list ID from the tracker list if the current <li>
        # element is the last element
        if (self.parent.element.getchildren()[-1] == self.element and
           isinstance(self, OrderedListItem)):
            del(ListItem.ListIDTracker[-1])

        # Adds list to the document
        self.parent.contents.addElement(self.parent.list)

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

    def convertTableContentToList(self, tableContent):
        # Create new OrderedList and give it a style
        ol = lxml.etree.Element('ol')
        ol.set('style', 'TableList')
        # Create style for the paragraph being created
        manager = attr.getManager(self)
        newParaStyleName = manager.getNextStyleName('TableListPara')
        newParaStyle = odf.style.Style(name=newParaStyleName)
        paraProps = odf.style.ParagraphProperties()
        paraProps.setAttribute('textalign', 'left')
        newParaStyle.appendChild(paraProps)
        manager.document.automaticstyles.addElement(newParaStyle)

        # Put contents of cell into the listitem elements
        for row in tableContent:
            bullet = row[0]
            content = row[1]
            olItem = lxml.etree.Element('li')
            olItem.set('bulletText', bullet)
            para = lxml.etree.Element('para')
            para.set('style', newParaStyleName)
            if '\n' in content:
                regex = "([0-9A-Za-z\t .,]+)"
                res = re.findall(regex, content)
                for i in range(len(res)):
                    if i == 0:
                        para.text = res[i].strip()
                    else:
                        br = lxml.etree.Element('br')
                        br.tail = res[i].strip()
                        para.append(br)
            else:
                para.text = content.strip()
            olItem.append(para)
            ol.append(olItem)
        # Add created list to the list of elements for processing
        self.element.append(ol)

    def extractTableContent(self):
        # Isolate all tables which occur within list items
        tables = [x for x in self.element.getchildren()
                  if x.tag == "blockTable"]
        for table in tables:
            tableContent = []
            self.element.remove(table)
            rows = table.getchildren()
            # Retrieve the data and store it in tableContent variable
            for row in rows:
                newLine = ""
                cells = row.getchildren()
                key = cells[0].text.strip()
                for cell in cells:
                    for para in cell.getchildren():
                        if para.text is not None:
                            newLine += para.text.strip()
                        for br in para.getchildren():
                            if br.tail is not None:
                                newLine += '\n'
                                newLine += br.tail.strip()
                value = newLine
                tableContent.append((key, value))
            self.convertTableContentToList(tableContent)

    def process(self):
        self.styleID = str(uuid.uuid4())
        self._convertSimpleContent()
        self.item = odf.text.ListItem()
        self.newStyleName = self.modifyStyle()
        self.createList()
        self.parent.list.addElement(self.item)
        self.contents = self.item
        super(ListItem, self).process()

        # Used to handle case where table appears in list item (never happened)
        # firstTable = [x for x in self.element.getchildren()
        #               if x.tag=="blockTable"][0]
        # firstTableIndex = self.element.getchildren().index(firstTable)
        # self.extractTableContent()
        # children = self.element.getchildren()
        # for i in range (len(children)):
        #     if i < firstTableIndex:
        #         self.element.remove(children[i])
        # super(ListItem, self).process()


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


class createStyle(object):

    def applyAttributes(self, attributes):
        if self.tag == "ul":
            new_style = ListStyle(name=self.name, consecutivenumbering=False)
            bulletList = UnorderedListItem.bulletList
            # listLevel-1 is used because the numbering of levels begins from 1
            # but the indexing of the bullet list starts at 0
            selectedBullet = bulletList[self.listLevel-1 % len(bulletList)]
            # XXX: Perhaps worry about list general bullet specifications
            bullet = ListLevelStyleBullet(
                level=str(self.listLevel),
                stylename="Standard",
                bulletchar=UnorderedListItem.bulletDict.get(
                    selectedBullet,
                    UnorderedListItem.bulletDict['disc'])
                )
            prop = ListLevelProperties(
                spacebefore=self.spacebefore,
                minlabelwidth="0.25in",
                **fontNameKeyword(attributes.get('bulletFontName'))
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
                **fontNameKeyword(attributes.get('bulletFontName'))
                )
            numstyle.addElement(prop)
            new_style.addElement(numstyle)
        return new_style

    def __init__(self, tag, listLevel, parent, attributes):
        self.parent = parent
        manager = attr.getManager(self)
        self.name = manager.getNextStyleName('Sh')
        # Tag is used later on for list specific processing
        self.tag = tag
        self.attributes = attributes
        self.listLevel = listLevel
        # May not be necessary unless fundamental override happens
        self.spacebefore = str(0.25*self.listLevel) + "in"
        self.new_style = createStyle.applyAttributes(self, self.attributes)
        manager.document.automaticstyles.addElement(self.new_style)


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

    def setStyleExtraProperties(self, existingStyleName):
        # Used when a list already has a style but has extra inline properties
        mapper = {
            'bulletType': 'numformat',
        }

        attrs = dict(self.getAttributeValues(attrMapping=mapper))
        if len(self.element.attrib) <= 1:
            return
        manager = attr.getManager(self)
        declaredStyles = manager.document.automaticstyles.childNodes
        for style in declaredStyles:
            attributes = style.attributes
            for key in attributes:
                if attributes[key] == existingStyleName:
                    for key in self.element.attrib:
                        if key != 'style':
                            value = self.element.attrib[key]
                            if style.childNodes:
                                if key in mapper:
                                    # XXX We ignore a lot here.
                                    style.childNodes[0].setAttribute(
                                        mapper[key], value)

    def determineStyle(self):
        # Checks if the list was supplied an already declared style
        existingStyleName = self.element.attrib.get('style')
        # Creates a new style if an existing style does not exist
        if existingStyleName is None:
            style = createStyle(self.element.tag, self.level, self.parent,
                                self.element.attrib)
            ListBase.createdStylesDict[self.styleID] = style.name
        else:
            # XXX: Find a way to check if provided styleNames have already
            # been initialized
            ListBase.createdStylesDict[self.styleID] = existingStyleName
            self.setStyleExtraProperties(existingStyleName)

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
