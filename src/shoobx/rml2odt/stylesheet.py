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
import copy
import odf.style
import odf.text
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
# from shoobx.rml2odt import flowable
from z3c.rml import stylesheet as rml_stylesheet



RML2ODT_ALIGNMENTS = {
    TA_LEFT: 'left',
    TA_CENTER: 'center',
    TA_RIGHT: 'right',
    TA_JUSTIFY: 'justify',
}

def pt(pt):
    return '%ipt' %pt

class Initialize(directive.RMLDirective):
    signature = rml_stylesheet.IInitialize
    factories = {
        'name': special.Name,
        'alias': special.Alias,
        }


def registerParagraphStyle(doc, name, rmlStyle):

    if 'style.' in name:
        name = name[6:]

    odtStyle = odf.style.Style(name=name, family='paragraph')
    doc.automaticstyles.addElement(odtStyle)

    # Paragraph Properties
    paraProps = odf.style.ParagraphProperties()
    odtStyle.addElement(paraProps)
    paraProps.setAttribute(
        'linespacing', pt(rmlStyle.leading))
    paraProps.setAttribute(
        'textalign', RML2ODT_ALIGNMENTS[rmlStyle.alignment])
    if rmlStyle.justifyLastLine:
        paraProps.setAttribute(
            'textalignlast', 'justify')
    paraProps.setAttribute(
        'textindent', pt(rmlStyle.firstLineIndent))
    paraProps.setAttribute(
        'widows', int(rmlStyle.allowWidows))
    paraProps.setAttribute(
        'orphans', int(rmlStyle.allowOrphans))
    paraProps.setAttribute(
        'marginleft', pt(rmlStyle.leftIndent))
    paraProps.setAttribute(
        'marginright', pt(rmlStyle.rightIndent))
    paraProps.setAttribute(
        'margintop', pt(rmlStyle.spaceBefore))
    paraProps.setAttribute(
        'marginbottom', pt(rmlStyle.spaceAfter))
    paraProps.setAttribute(
        'borderlinewidth', pt(rmlStyle.borderWidth))
    paraProps.setAttribute(
        'padding', pt(rmlStyle.borderPadding))



    # Text Properties
    textProps = odf.style.TextProperties()
    odtStyle.addElement(textProps)

    if rmlStyle.fontName is not None:
        
        doc.fontfacedecls.addElement(
            odf.style.FontFace(
                name=rmlStyle.fontName,
                fontfamily=rmlStyle.fontName))
        textProps.setAttribute('fontname', rmlStyle.fontName)
    textProps.setAttribute('fontsize', rmlStyle.fontSize)

    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#'+rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute('backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])
    
 

    # Unsupported options:
    
    # - bulletFontSize
    # - bulletIndent
    # - bulletColor
    # - wordWrap
    # - borderRadius
    # - textTransform
    # - endDots
    # - splitLongWords
    # - underlineProportion
    # - bulletAnchor
    # - justifyBreaks
    # - spaceShrinkage

def registerListStyle(doc, attributes):
    name = attributes.get('name', 'undefined')
    bulletType = attributes.get('start', 'disc')
    fontSize = attributes.get('bulletFontSize', '12')
    fontName = attributes.get('bulletFontName', 'Arial')
    bulletColor = attributes.get('bulletColor', 'black')
    bulletDict = {
    'disc':u'\u25CF',
    'square':u'\u25A0',
    'diamond':u'\u25C6',
    'rarrowhead': u'\u27A4',
    }

    # Create new sttyle object
    odtStyle = odf.text.ListStyle(name=name)
    # Create new bullet object
    try:
        retrievedBullet = bulletDict[bulletType]
    except:
        retrievedBullet = bulletType
    bullet = odf.text.ListLevelStyleBullet(
        bulletchar = retrievedBullet, 
        level=1, 
        stylename="Standard")
    # Declare properties of the list style
    # You can declare fontname here (which should be supplied as an attribute)
    listProps = odf.style.ListLevelProperties(minlabelwidth='0.25in')


    # if rmlStyle.bulletFontName is not None:
    #     doc.automaticstyles.addElement(
    #         odf.text.ListStyle(
    #             name = rmlStyle.bulletFontName))
    #     listProps.setAttribute('fontname',rmlStyle.bulletFontName)

    # Add properties to created bullet style object
    bullet.addElement(listProps)
    # Add bullet object to created style
    odtStyle.addElement(bullet)
    # Finally, add style to collection of styles (which can be accessed anywhere)
    # in the document
    doc.automaticstyles.addElement(odtStyle)
    

class ParagraphStyle(directive.RMLDirective):
    signature = rml_stylesheet.IParagraphStyle


    

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', SampleStyleSheet['Normal'])
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name
        for attrName, attrValue in kwargs.items():
            setattr(style, attrName, attrValue)
        document = self.parent.parent.document
        registerParagraphStyle(document, name, style)
            


            

class ListStyle(directive.RMLDirective):
    signature = rml_stylesheet.IListStyle

    def process(self):
        attributeDict = self.element.attrib
        document=self.parent.parent.document
        registerListStyle(document, attributeDict)


class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        #'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
        }