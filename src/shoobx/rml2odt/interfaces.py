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
"""RML to ODT Converter Interfaces
"""
import zope.interface


class IRML2ODT(zope.interface.Interface):
    """This is the main public API of shoobx.rml2odt"""

    def convertString(rml, remove_encoding=True, filename=None):
        """Parse an RML string and convert it to ODT.

        The output is a ``StringIO`` object.
        """

    def convertFile(inputfile, outputfile):
        """Convert an RML file to an ODT file.
        """


class IContentContainer(zope.interface.Interface):
    """Content Container"""

    contents = zope.interface.Attribute(
        'Container to which content, such as paragraphs and tables can be '
        'added.')
