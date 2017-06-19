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
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from shoobx.rml2odt import flowable
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
    odtStyle = odf.style.Style(name=name, family='paragraph')
    doc.styles.addElement(odtStyle)

    # Paragraph Properties
    paraProps = odf.style.ParagraphProperties()
    paraProps.setAttribute(
        'linespacing', pt(rmlStyle.leading))
    paraProps.setAttribute(
        'textalign', RML2ODT_ALIGNMENTS[rmlStyle.alignment])
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

    # Text Properties
    textProps = odf.style.TextProperties()
    odtStyle.addElement(textProps)
    textProps.setAttribute('fontname', rmlStyle.fontName)
    textProps.setAttribute('fontsize', rmlStyle.fontSize)

    if rmlStyle.textColor is not None:
        textProps.setAttribute('color', '#'+rmlStyle.textColor.hexval()[2:])
    if rmlStyle.backColor is not None:
        textProps.setAttribute(
            'backgroundcolor', '#'+rmlStyle.backColor.hexval()[2:])

    # Unsupported options:
    # - bulletFontName
    # - bulletFontSize
    # - bulletIndent
    # - bulletColor
    # - wordWrap
    # - borderWidth
    # - borderPadding
    # - borderColor
    # - borderRadius
    # - allowOrphans
    # - textTransform
    # - endDots
    # - splitLongWords
    # - underlineProportion
    # - bulletAnchor
    # - justifyLastLine
    # - justifyBreaks
    # - spaceShrinkage


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
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', reportlab.lib.styles.ListStyle(name='List'))
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name

        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style


class Stylesheet(directive.RMLDirective):
    signature = rml_stylesheet.IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        # XXX: Unsupported elements:
        #'blockTableStyle': BlockTableStyle,
        #'listStyle': ListStyle,
        }
