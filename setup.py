# -*- coding: utf-8 -*-
"""
A DSL for extracting data from a web page. The DSL serves two purposes:
finds elements and extracts their text or attribute values. The main
reason for developing this is to have all the CSS selectors for scraping
a site in one place (I prefer CSS selectors over anything else).

The DSL wraps `PyQuery`_.

.. _PyQuery: https://pythonhosted.org/pyquery/index.html
"""
import ast
import re
from setuptools import setup


_version_re = re.compile(r'^__version__\s+=\s+(.*)$', re.MULTILINE)

with open('take/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open('README.rst', 'rb') as f:
    long_desc = f.read().decode('utf-8')


setup(
    name='take',
    version=version,
    url='https://github.com/tiffon/take',
    license='MIT',
    author='Joe Farro',
    author_email='joe@jf.io',
    description='A DSL for extracting data from a web page.',
    long_description=long_desc,
    # I hear eggs are bad
    zip_safe=False,
    classifiers=[
        # status of this dist
        'Development Status :: 3 - Alpha',
        # for who
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        # for what
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities',
        # could be a nice companion util with scrapy
        'Framework :: Scrapy',
        # license
        'License :: OSI Approved :: MIT License',
        # env
        'Operating System :: OS Independent',
        # python versions
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='scraping scrapy scraper extraction html',
    packages=['take'],
    install_requires=[
        "cssselect==0.9.1",
        "enum34==1.0.4",
        "lxml==3.4.2",
        "pyquery==1.2.9"
    ],
    include_package_data=True
)
