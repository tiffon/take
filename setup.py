"""
A DSL for extracting data from a web page. The DSL serves two purposes: finds
elements and extracts their text or attribute values. The main reason for developing
this is to have all the CSS selectors for scraping a site in one place.

The DSL wraps `PyQuery`_.


Example
-------

Given the following take template:

    $ h1 | text
        save: h1_title
    $ ul
        save each: uls
            $ li
                | 0 [title]
                    save: title
                | 1 text
                    save: second_li
    $ p | 1 text
        save: p_text

And the following HTML:

    <div>
        <h1>Le Title 1</h1>
        <p>Some body here</p>
        <h2 class="second title">The second title</h2>
        <p>Another body here</p>
        <ul id="a">
            <li title="a less than awesome title">A first li</li>
            <li>A second li</li>
            <li>A third li</li>
        </ul>
        <ul id="b">
            <li title="some awesome title">B first li</li>
            <li>B second li</li>
            <li>B third li</li>
        </ul>
    </div>

The following data will be extracted (presented in JSON format):

    {
        "h1_title": "Le Title 1",
        "p_text": "Another body here",
        "uls": [
            {
                "title": "a less than awesome title",
                "second_li": "A second li"
            },
            {
                "title": "some awesome title",
                "second_li": "B second li"
            }
        ]
    }

Take templates always result in a single python `dict`.

For a more complex example, see the `reddit sample`_.

.. _PyQuery: https://pythonhosted.org/pyquery/index.html
.. _reddit sample: https://github.com/tiffon/take/blob/master/take/sample.py
"""

from setuptools import setup

VERSION = '0.0.0'

setup(
    name='take',
    version=VERSION,
    url='https://github.com/tiffon/take',
    license='MIT',
    author='Joe Farro',
    author_email='joe@jf.io',
    description='A DSL for extracting data from a web page.',
    long_description=__doc__,
    # I hear eggs are bad
    zip_safe=False,
    # TODO: more classifiers
    classifiers=[
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    packages=['take'],
    install_requires=[
        "cssselect==0.9.1",
        "enum34==1.0.4",
        "lxml==3.4.2",
        "pyquery==1.2.9"
    ],
    include_package_data=True
)
