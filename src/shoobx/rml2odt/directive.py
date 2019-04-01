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
"""RML Directive Implementations
"""
import lxml

from z3c.rml import directive


class NotImplementedDirective(directive.RMLDirective):

    def process(self):
        raise NotImplementedError(
            u'Directive not implemented: %s' % self.element.tag)


class BaseDirective(directive.RMLDirective):

    def processSubDirectives(self, select=None, ignore=None):
        # Go through all children of the directive and try to process them.
        for element in self.element.getchildren():
            tag = element.tag
            # IN CONTRAST to z3c.rml
            # Process all comments, tag tail needs to be included as text!
            # pain is that the element.tag is some weird method
            if isinstance(element, lxml.etree._Comment):
                tag = '__comment__'
            # Raise an error/log any unknown directive.
            if tag not in self.factories:
                msg = "Directive %r could not be processed and was " \
                      "ignored. %s" %(tag, directive.getFileInfo(self, element))
                # Record any tags/elements that could not be processed.
                directive.logger.warning(msg)
                if directive.ABORT_ON_INVALID_DIRECTIVE:
                    raise ValueError(msg)
                continue
            if select is not None and tag not in select:
                continue
            if ignore is not None and tag in ignore:
                continue
            handler = self.factories[tag](element, self)
            handler.process()
