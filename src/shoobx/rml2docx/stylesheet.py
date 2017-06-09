##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special

from z3c.rml import stylesheet as rml_stylesheet

class Initialize(directive.RMLDirective):
    signature = rml_stylesheet.IInitialize
    factories = {
        'name': special.Name,
        'alias': special.Alias,
        }

class ParagraphStyle(directive.RMLDirective):
    signature = rml_stylesheet.IParagraphStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', SampleStyleSheet['Normal'])
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name

        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style

class TableStyleCommand(directive.RMLDirective):
    name = None

    def process(self):
        args = [self.name]
        args += self.getAttributeValues(valuesOnly=True)
        self.parent.style.add(*args)

class BlockFont(TableStyleCommand):
    signature = rml_stylesheet.IBlockFont
    name = 'FONT'

class BlockLeading(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeading
    name = 'LEADING'

class BlockTextColor(TableStyleCommand):
    signature = rml_stylesheet.IBlockTextColor
    name = 'TEXTCOLOR'

class BlockAlignment(TableStyleCommand):
    signature = rml_stylesheet.IBlockAlignment
    name = 'ALIGNMENT'

class BlockLeftPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockLeftPadding
    name = 'LEFTPADDING'

class BlockRightPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockRightPadding
    name = 'RIGHTPADDING'

class BlockBottomPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockBottomPadding
    name = 'BOTTOMPADDING'

class BlockTopPadding(TableStyleCommand):
    signature = rml_stylesheet.IBlockTopPadding
    name = 'TOPPADDING'

class BlockBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockBackground
    name = 'BACKGROUND'

    def process(self):
        args = [self.name]
        if 'colorsByRow' in self.element.keys():
            args = [BlockRowBackground.name]
        elif 'colorsByCol' in self.element.keys():
            args = [BlockColBackground.name]

        args += self.getAttributeValues(valuesOnly=True)
        self.parent.style.add(*args)

class BlockRowBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockRowBackground
    name = 'ROWBACKGROUNDS'

class BlockColBackground(TableStyleCommand):
    signature = rml_stylesheet.IBlockColBackground
    name = 'COLBACKGROUNDS'

class BlockValign(TableStyleCommand):
    signature = rml_stylesheet.IBlockValign
    name = 'VALIGN'

class BlockSpan(TableStyleCommand):
    signature = rml_stylesheet.IBlockSpan
    name = 'SPAN'

class LineStyle(TableStyleCommand):
    signature = rml_stylesheet.ILineStyle

    def process(self):
        name = self.getAttributeValues(select=('kind',), valuesOnly=True)[0]
        args = [name]
        args += self.getAttributeValues(ignore=('kind',), valuesOnly=True,
                                        includeMissing=True)
        self.parent.style.add(*args)

class BlockTableStyle(directive.RMLDirective):
    signature = rml_stylesheet.IBlockTableStyle

    factories = {
        'blockFont': BlockFont,
        'blockLeading': BlockLeading,
        'blockTextColor': BlockTextColor,
        'blockAlignment': BlockAlignment,
        'blockLeftPadding': BlockLeftPadding,
        'blockRightPadding': BlockRightPadding,
        'blockBottomPadding': BlockBottomPadding,
        'blockTopPadding': BlockTopPadding,
        'blockBackground': BlockBackground,
        'blockRowBackground': BlockRowBackground,
        'blockColBackground': BlockColBackground,
        'blockValign': BlockValign,
        'blockSpan': BlockSpan,
        'lineStyle': LineStyle,
        }

    def process(self):
        kw = dict(self.getAttributeValues())
        id  = kw.pop('id')
        # Create Style
        self.style = reportlab.platypus.tables.TableStyle()
        for name, value in kw.items():
            setattr(self.style, name, value)
        # Fill style
        self.processSubDirectives()
        # Add style to the manager
        manager = attr.getManager(self)
        manager.styles[id] = self.style

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
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
        }
