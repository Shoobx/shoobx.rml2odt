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
"""Setup
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


def alltests():
    import os
    import sys
    import unittest
    # use the zope.testrunner machinery to find all the
    # test suites we've put under ourselves
    import zope.testrunner.find
    import zope.testrunner.options
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    args = sys.argv[:]
    defaults = ["--test-path", here]
    options = zope.testrunner.options.get_options(args, defaults)
    suites = list(zope.testrunner.find.find_suites(options))
    return unittest.TestSuite(suites)


TESTS_REQUIRE = [
    'coverage',
    'unoconv',
    'zope.testrunner',
    ]


setup(
    name="shoobx.rml2odt",
    version='0.5.0',
    author="Shoobx, Inc.",
    author_email="dev@shoobx.com",
    description="A converter from RML to ODT.",
    long_description=(
        read('README.rst')
        + '\n\n' +
        read('CHANGES.rst')
        ),
    license="ZPL 2.1",
    keywords="rml odf odt libreoffice pagetemplate",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    url='http://pypi.python.org/pypi/shoobx.rml2odt',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['shoobx'],
    extras_require=dict(
        test=TESTS_REQUIRE,
        ),
    install_requires=[
        'lazy',
        'odfpy',
        'pypng',
        'PyQRCode',
        'setuptools',
        'six',
        'z3c.rml',
        'zope.interface',
        ],
    entry_points={
        'console_scripts': [
            'rml2odt = shoobx.rml2odt.rml2odt:main'
            ],
        },
    tests_require=TESTS_REQUIRE,
    test_suite='__main__.alltests',
    include_package_data=True,
    zip_safe=False,
    )
