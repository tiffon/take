A DSL for extracting data from a web page. The DSL serves two purposes:
finds elements and extracts their text or attribute values. The main
reason for developing this is to have all the CSS selectors for scraping
a site in one place (I prefer CSS selectors over anything else).

The DSL wraps `PyQuery`_.

A few links:

* `Github repository <https://github.com/tiffon/take>`_

* `PyPi package <https://pypi.python.org/pypi/take>`_

* `Discussion group <https://groups.google.com/forum/#!forum/take-dsl>`_

Example
-------

Given the following take template:

::

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

.. code:: html

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

.. code:: json

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

Take templates always result in a single python ``dict``.

For a more complex example, see the `reddit sample`_.

Install
-------

.. code::

    pip install take


Usage
-----

Creating a Take Template
^^^^^^^^^^^^^^^^^^^^^^^^

A take template can be created from either a ``basestring`` or an
``Iterable`` that will return one line per iteration.

To create a template from a file:

.. code:: python

    from take import TakeTemplate
    with open('yourfile.take') as f:
        tt = TakeTemplate(f)

To create a template from a string:

.. code:: python

    from take import TakeTemplate
    TMPL = """
    $ nav a
        save each: nav
            | text
                save: text
            | [href]
                save: link
    """
    tt = TakeTempalte(TMPL)

Additionally, a ``base_url`` keyword argument can be specified which
will cause relative URLs to be made absolute via the value of the
``base_url`` parameter for any documents that are processed.

.. code:: python

    tt = TakeTempalte(TMPL, base_url='http://www.example.com')

If a ``base_url`` is provided when the template is used, it will
override the ``base_url`` provided when the template was created. The
``base_url`` parameter must be provided as a keyword argument.

Using a Take Template
^^^^^^^^^^^^^^^^^^^^^

To parse from a URL:

.. code:: python

    data = tt(url='http://www.example.com')

To parse from a html string:

.. code:: python

    data = tt('<div>hello world</div>')

To parse from a file:

.. code:: python

    data = tt(filename=path_to_html_file)

Alternatively, the ``take()`` method can be used:

.. code:: python

    data = tt.take(url='http://www.example.com')

Valid parameters for the template callable or the ``take()`` method are
the same as those for the `PyQuery constructor`_.

Additionally, if the ``'base_url'`` keyword parameter is supplied, all
relative URLs will be made absolute via the value of ``'base_url'``.

.. code:: python

    data = tt(url='http://www.example.com', base_url='http://www.example.com')

Take Templates
--------------

Take templates are whitespace sensitive and are comprised of three types
of lines:

-  A query

   -  ``$ h1``

   -  ``| text``

   -  ``$ h1 | 0 text``

-  A ``save`` directive

   -  ``save: h1_title``

   -  ``save: time.exact``

-  A ``save each`` directive

   -  ``save each: entries``

   -  ``save each: popular.movies``

Queries
-------

There are two main types of queries in take templates:

-  CSS selector queries

-  Non-CSS selector queries

The reason they’re divided like this is because CSS Selectors always go
first on the line and they can be followed by non-CSS non-CSS Selector queries.
Non-CSS selector queries can’t be followed by CSS selector queries.
Seems easier to read this way, but it’s arbitrary and may change.

CSS Selector queries
^^^^^^^^^^^^^^^^^^^^

CSS selector queries start with ``$`` and end either at the end of the
line or at the ``|`` character. The ``|`` character delimits non-CSS
selector queries.

-  ``$ #siteTable .thing | text``
-  ``$ .domain a``

In the first example above, the CSS selector query is
``#siteTable .thing``. The second is ``.domain a``.

The CSS selectors are passed to `PyQuery`_, so anything PyQuery can
accept can be used. From what I understand, there are a few `bugs`_ in
PyQuery (that may be in the underlying libraries `lxml`_ or
`cssselect`_). Those will come up.

Non-CSS Selector queries
^^^^^^^^^^^^^^^^^^^^^^^^

Non-CSS selector queries start with ``|`` and continue for the rest of
the line. There are three non-CSS Selector queries:

-  Element indexes

   -  Syntax: an integer

   -  ``| 0`` will return the first element in the current context

   -  ``| 1`` will return the second element in the current context

-  Text retrieval

   -  Syntax: ``text``

   -  ``| text`` will return the text of the current context

   -  ``| 1 text`` will first get the second element in the current context
      and then return it’s text

-  Attribute retrieval

   -  Syntax: ``[attr]``

   -  ``| [href]`` will return the value of the ``href`` attribute of the
      first element in the current context

   -  ``| 1 [href]`` will return the value of the ``href`` attribute of the
      second element in the current context

**Order matters**: Index queries should precede text or attribute
retrieval queries. Only one of text or attribute queries can be used;
they can’t both be used on one line.

Whitespace
----------

The level of indentation on each line defines the context for the line.

The root context of a take template is the current document being
processed. Every statement that is not indented is executed against the
document being processed.

Each line that is indented more deeply has a context that is the result
of the last query in the parent context. For example:

::

    $ #some-id
        $ li
        $ div

The query on the first line is executed against the document being
processed. The query on the second line is executed against the result
of the first line. So, the second line is synonomous with
``$ #some-id li``. The query on the third line is also executed against
the result of the first line. So, it can be re-written as
``$ #some-id div``.

Another example:

::

    $ a
        | 0
            | text
            | [href]

The third and fourth lines retrieve the text and href attribute,
respectively, from the first ``<a>`` in the document being processed.
This could be rewritten as:

::

    $ a | 0
        | text
        | [href]

Save Directives
---------------

Save directives save the context into the result ``dict``. These are
generally only intended to be applied to the result of a ``text`` or
``[attr]`` retrieval.

Their syntax is:

::

    save: identifier

Any non-whitespace characters can be used as the identifier. Also, the
identifier can contain dots (``.``), which designate sub-\ ``dicts`` for
saving.

For example, the following take template:

::

    $ a | 0
        | text
            save: first_a.text
        | [href]
            save: first_a.href

And the following HTML:

.. code:: html

    <div>
        <a href="http://www.example.com">fo sho</a>
        <a href="http://www.another.com">psych out</a>
    </div>

Will result in the following python ``dict``:

.. code:: python

    {
        'first_a': {
            'text': 'fo sho',
            'href': 'http://www.example.com'
        }
    }

Save Each Directives
--------------------

Save each directives produce a list of dicts. Generally, these are used
for repeating elements on a page. In the reddit sample, a save each
directive is used to save each of the reddit entries.

Their syntax is:

::

    save each: identifier

Any non-whitespace characters can be used as the identifier. Also, the
identifier can contain dots (``.``), which designate sub-\ ``dicts`` for
saving.

Save each directives apply the next sub-context to each of the elements
of their context. Put another way, save each directives repeatedly
process each element of thier context.

For example, in the following take template, the ``| text`` and
``| [href]`` queries (along with saving the results) will be applied to
every ``<a>`` in the document.

::

    $ a
        save each: anchors
            | text
                save: text
            | [href]
                save: href

Applying the above take template to the following HTML:

.. code:: html

    <div>
        <a href="http://www.example.com">fo sho</a>
        <a href="http://www.another.com">psych out</a>
    </div>

Will result in the following python ``dict``:

.. code:: python

    {
        'anchors': [{
                'text': 'fo sho',
                'href': 'http://www.example.com'
            },{
                'text': 'psych out',
                'href': 'http://www.another.com'
            }
        ]
    }

.. _PyQuery: https://pythonhosted.org/pyquery/index.html
.. _reddit sample: https://github.com/tiffon/take/blob/master/take/sample.py
.. _PyQuery constructor: https://pythonhosted.org/pyquery/index.html#quickstart
.. _bugs: https://github.com/gawel/pyquery/issues
.. _lxml: http://lxml.de/
.. _cssselect: https://pythonhosted.org/cssselect/
