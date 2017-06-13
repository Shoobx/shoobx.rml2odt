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
import six
import pdb
import zope.interface
<<<<<<< Updated upstream
from z3c.rml import directive, interfaces
from z3c.rml import template as rml_template
from z3c.rml import page as rml_page


=======
from reportlab import platypus
from z3c.rml import directive, attr, interfaces, occurence
from z3c.rml import template as rml_template
>>>>>>> Stashed changes
from shoobx.rml2docx import flowable
from z3c.rml import canvas, stylesheet
from z3c.rml import page as rml_page
 
 
class Story(flowable.Flow):
    signature = rml_template.IStory
    # def container seems to bring in code from the tox directive
    #from which it was called
    @property
    def container(self):
        return self.parent.document
 
# class Template(directive.RMLDirective): 
# 	signature = rml_template.ITemplate 
 
# 	factories = {
#     'pageTemplate': rml_template.PageTemplate
#     }
 
# 	@property
# 	def container(self):
# 		return self.parent.document
 
@zope.interface.implementer(interfaces.ICanvasManager)
class PageGraphics(directive.RMLDirective):
    signature = rml_template.IPageGraphics

    @property
    def container(self):
        return self.parent.document
<<<<<<< Updated upstream

=======
 
    # def process(self):
    #     onPage = self.parent.pt.onPage
    #     def drawOnCanvas(canv, doc):
    #         onPage(canv, doc)
    #         canv.saveState()
    #         self.canvas = canv
    #         drawing = canvas.Drawing(self.element, self)
    #         drawing.process()
    #         canv.restoreState()
 
    #     self.parent.pt.onPage = drawOnCanvas
 
>>>>>>> Stashed changes
class Frame(directive.RMLDirective):
    signature = rml_template.IFrame

    @property
    def container(self):
        return self.parent.document
<<<<<<< Updated upstream

@zope.interface.implementer(interfaces.ICanvasManager)
class PageGraphics(directive.RMLDirective):
    signature = rml_template.IPageGraphics

    @property
    def container(self):
        return self.parent.document

=======
 
    # def process(self):
    #     #get the page size
    #     size = self.parent.pt.pagesize
    #     if size is None:
    #         size = self.parent.parent.parent.doc.pagesize
    #     #get the arguments
    #     args = dict(self.getAttributeValues())
    #     #Deal with percentages
    #     for name, dir in (('x1', 0), ('y1', 1), ('width', 0), ('height', 1)):
    #         if isinstance(args[name], six.string.types) and args[name].endswith('%'):
    #             args[name] = float(args[name][:-1])/100*size[dir]
    #     frame = platypus.Frame(**args)
    #     self.parent.frames.append(frame)
 
>>>>>>> Stashed changes
class PageTemplate(directive.RMLDirective):
    signature = rml_template.IPageTemplate
    attrMapping = {'autoNextTemplate': 'autoNextPageTemplate'}
    factories = {
<<<<<<< Updated upstream
        'frame': Frame,
        'pageGraphics': PageGraphics,
        'mergePage': rml_page.MergePageInPageTemplate,
        }
=======
    'frame': Frame,
    'pageGraphics': PageGraphics
    # 'mergePage': page.MergePageInTemplate,
    }
>>>>>>> Stashed changes

    @property
    def container(self):
        return self.parent.document
<<<<<<< Updated upstream

class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    factories = {
        'pageTemplate': PageTemplate,
        }


    @property
    def container(self):
        return self.parent.document
=======
 
    # def process(self):
    #     args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
    #     pagesize = args.pop('pagesize', None)
 
    #     self.frames = []
    #     self.pt = platypus.PageTemplate(**agrs)
 
    #     self.processSubDirectives()
    #     self.pt.frames = self.frames
 
    #     if pagesize:
    #         self.pt.pagesize = pagesize
 
    #     self.parent.parent.doc.addPageTemplates(self.pt)
 
 
class Template(directive.RMLDirective):
    signature = rml_template.ITemplate
    factories = {
    'pageTemplate': PageTemplate,
    }

    # @property
    # def container(self):
    #     return self.parent.document
    
 
    def process(self):
        args = self.getAttributeValues()
        # pdb.set_trace()
        args += self.parent.getAttributeValues(
            select=('debug', 'compression', 'invariant'),
            attrMapping={'debug': '_debug', 'compression': 'pageCompression'})
        # args += (('cropMarks',  self.parent.cropMarks),)
        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
>>>>>>> Stashed changes
