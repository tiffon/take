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
        <p>The second body here</p>
        <ul id="a">
            <li title="a less than awesome title">A first li</li>
            <li>Second li in list #a</li>
            <li>A third li</li>
        </ul>
        <ul id="b">
            <li title="some awesome title">B first li</li>
            <li>Second li in list #b</li>
            <li>B third li</li>
        </ul>
    </div>

The following data will be extracted (presented in JSON format):

.. code:: json

    {
        "h1_title": "Le Title 1",
        "p_text": "The second body here",
        "uls": [
            {
                "title": "a less than awesome title",
                "second_li": "Second li in list #a"
            },
            {
                "title": "some awesome title",
                "second_li": "Second li in list #b"
            }
        ]
    }

Take templates always result in a single python ``dict``.

The template can also be written in the following, more concise, syntax:

::

    $ h1 | text ;                   : h1_title
    $ ul
        save each                   : uls
            $ li
                | 0 [title] ;           : title
                | 1 text ;              : second_li
    $ p | 1 text ;                  : p_text

The example above is formatted with extra whitespace to make the structure
of the resulting data more apparent.

More Examples
^^^^^^^^^^^^^

For more complex examples:

-  Scraping the `reddit home page <http://www.reddit.com/>`_

   -  `Inline version <https://github.com/tiffon/take/blob/master/sample/reddit_inline_saves.take>`_

   -  `Verbose version <https://github.com/tiffon/take/blob/master/sample/reddit.take>`_

-  Scraping the latest `web-scraping questions <http://stackoverflow.com/questions/tagged/web-scraping?sort=newest&pageSize=10>`_ on Stack Overflow:

   -  `Overview <https://github.com/tiffon/take-examples/tree/master/samples/stackoverflow>`_

   -  `questions-listing.take <https://github.com/tiffon/take-examples/blob/master/samples/stackoverflow/questions-listing.take>`_

   -  `question-page.take <https://github.com/tiffon/take-examples/blob/master/samples/stackoverflow/question-page.take>`_

Install
-------

.. code::

    pip install take


Usage
-----

Creating a Take Template
^^^^^^^^^^^^^^^^^^^^^^^^

A take template can be created from a file via the static method
``TakeTemplate.from_file()``.

.. code:: python

    from take import TakeTemplate
    tt = TakeTemplate.from_file('yourfile.take')

The ``TakeTemplate`` constructor can be used to create a template from either
a ``basestring`` or an ``Iterable``.

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
    tt = TakeTemplate(TMPL)

Additionally, a ``base_url`` keyword argument can be specified which
will cause relative URLs to be made absolute via the value of the
``base_url`` parameter for any documents that are processed.

.. code:: python

    tt = TakeTemplate.from_file('yourfile.take', base_url='http://www.example.com')

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
of statements:

-  Comment Lines

   -  ``# some comment``

-  Queries

   -  ``$ h1``

   -  ``| text``

   -  ``$ h1 | 0 text``

-  Directives

   -  ``save: h1_title``

   -  ``save each: comments``

   -  ``merge: *``

   -  ``def: get comments``

Comment Lines
-------------

Any line with a ``#`` as the first non-whitespace character is considered a comment line.

::

    # this line is a comment
    # the third line is a CSS selector query
    $ #main-nav a

Comment lines are completely ignored. Partially commented lines and multi-line comments are not supported at this time.

Queries
-------

There are two main types of queries in take templates:

-  CSS selector queries

-  Non-CSS selector queries

The reason they’re divided like this is because CSS selectors always go
first on the line and they can be followed by non-CSS selector queries.
Non-CSS selector queries can’t be followed by CSS selector queries.
Seems easier to read this way, but it’s arbitrary and may change.

CSS Selector Queries
^^^^^^^^^^^^^^^^^^^^

CSS selector queries start with ``$`` and end either at the end of the
line, the ``|`` character or the ``;`` character. The ``|`` character
is the starting character for non-CSS selector queries, and the ``;``
character ends the statement and starts an `inline sub-context <#inline-sub-contexts>`_.

-  ``$ #siteTable .thing | text``
-  ``$ .domain a``

In the first example above, the CSS selector query is
``#siteTable .thing``. The second is ``.domain a``.

The CSS selectors are passed to `PyQuery`_, so anything PyQuery can
accept can be used. From what I understand, there are a few `bugs`_ in
PyQuery (that may be in the underlying libraries `lxml`_ or
`cssselect`_). Those will come up.

Non-CSS Selector Queries
^^^^^^^^^^^^^^^^^^^^^^^^

Non-CSS selector queries start with ``|`` and continue until the ``;`` character or the
line ends. There are five non-CSS selector queries:

-  **Element indexes**

   -  Syntax: an integer

   -  ``| 0`` will return the first element in the current context

   -  ``| 1`` will return the second element in the current context

   -  ``| -1`` will return the last element in the current context

-  **Attribute retrieval**

   -  Syntax: ``[attr]``

   -  ``| [href]`` will return the value of the ``href`` attribute of the
      first element in the current context

   -  ``| 1 [href]`` will return the value of the ``href`` attribute of the
      second element in the current context

-  **Text retrieval**

   -  Syntax: ``text``

   -  ``| text`` will return the text of the current context

   -  ``| 1 text`` will first get the second element in the current context
      and then return it’s text

-  **Own text retrieval**

   -  Syntax: ``own_text``

   -  ``| own_text`` will return the text of the current context without the text
      from its children

   -  ``| 1 own_text`` will first get the second element in the current context
      and then return it’s text without the text from its children

-  **Field retrieval**

   -  Syntax: ``.field_name``

   -  ``| .description`` will do a dictionary lookup on the context and retrieve
      the value of the ``'description'`` item

   -  ``| .parent.child`` will do a dictionary lookup on the context and retrieve
      the value of the ``'parent'`` and then it will lookup ``'child'`` on that value

**Order matters**: Index queries should precede other queries. Also, only one
of ``[attr]``, ``text``, ``own_text`` or ``.field_name`` queries can be used.

Indentation
-----------

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

Inline Sub Contexts
^^^^^^^^^^^^^^^^^^^

Inline sub-contexts allow multuple statements per line. The syntax is:

::

    statement ; sub-context-statement

The main thing to note is: whatever comes after the semi-colin is treated as if it were a line with deeper indentation.

Inline sub-contexts are primarily used with directives. For example, the following take template:

::

    $ h1 | 0 text
        save: section_title

Can be re-written as:

::

    $ h1 | 0 text ; save: document_title

Both templates save the text in the first ``<h1>`` element into the result ``dict`` with the key ``'document_title'``. More on `save directives <#save-directive>`_ later.

Directives
----------

Directives are commands that are executed against the current context.
They're format is a directive name followed by an optional parameter list:

::

    <directive_name> [: <parameter>[<whitespace or comma> <parameter>]*]?

An example of a ``save`` directive:

::

    save : some_name

Not all directives require parameters. For example, the ``shrink`` directive,
which collapses whitespace, does not:

::

    shrink

The following directives are built-in:

-  ``save``, alias ``:``

   -  Saves a value.

-  ``save each``

   -  Creates a list of results.

-  ``namespace``, alias ``+``

   -  Creates child ``dict`` for saving values into.

-  ``shrink``

   -  Collapses and trims whitespace.

-  ``def``

   -  Defines a new directive. *Currently only new directives defined in the current document are available.*

-  ``merge``, alias ``>>``

   -  Copies a value from a directive's result into the template's result.

Save Directive
^^^^^^^^^^^^^^

*Alias:* ``:``

Save directives save the context into the result ``dict``. These are
generally only intended to be applied to the result of non-CSS Selector
queries.

The syntax is:

::

    save: <identifier>

``:`` is an alias for ``save:``. So, a save directive can also be written as:

::

    : <identifier>

The identifier can contain anything except whitespace, a comma (``,``) or a semi-colin (``;``).
Also, the identifier can contain dots (``.``), which designate sub-\ ``dicts`` for
saving.

For example, the following take template:

::

    $ a | 0
        | text
            save: first_a.description
        | [href]
            save: first_a.url

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
            'description': 'fo sho',
            'url': 'http://www.example.com'
        }
    }

Using the ``:`` alias, the template can be written as:

::

    $ a | 0
        | text
            : first_a.text
        | [href]
            : first_a.href

Or, more succinctly:

::

    $ a | 0
        | text ;        : first_a.text
        | [href] ;      : first_a.href

Save Each Directive
^^^^^^^^^^^^^^^^^^^

Save each directives produce a ``dict`` for each element in the context. Generally, these are used for repeating elements on a page. In the `reddit sample <https://github.com/tiffon/take/blob/master/sample/reddit_inline_saves.take>`_, a save each directive is used to save each of the reddit entries.

The syntax is:

::

    save each: <identifier>
        <sub-context>

The identifier can contain anything except whitespace, a comma (``,``) or a semi-colin (``;``).
Also, the identifier can contain dots (``.``), which designate sub-\ ``dict``\ s for
saving.

Save each directives apply the next sub-context to each of the elements
of their context value. Put another way, save each directives repeatedly
process each element of their context.

For example, in the following take template, the ``| text`` and
``| [href]`` queries (along with saving the results) will be applied to
every ``<a>`` in the document.

::

    $ a
        save each: anchors
            | text
                save: description
            | [href]
                save: url

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
                'description': 'fo sho',
                'url': 'http://www.example.com'
            },{
                'description': 'psych out',
                'url': 'http://www.another.com'
            }
        ]
    }

Namespace Directive
^^^^^^^^^^^^^^^^^^^

*Alias:* ``+``

Namespace directives create a sub-``dict`` on the current result-value and everyting in the
next sub-context is saved into the new ``dict``.

The syntax is:

::

    namespace: <identifier>
        <sub-context>

``<identifier>`` is the key the sub-``dict`` is saved as.

An example:

::

    $ a | 0
        namespace: first_a
            | text
                save: description
            | [href]
                save: url

Applying the above take template to the following HTML:

.. code:: html

    <div>
        <a href="http://www.example.com">fo sho</a>
        <a href="http://www.another.com">psych out</a>
    </div>

Will result in the following python ``dict``:

.. code:: python

    {
        'first_a': {
            'description': 'fo sho',
            'url': 'http://www.example.com'
        }
    }

The ``description`` and ``url`` fields are saved in the ``first_a`` namespace. This reduces
the need for save directives like: ``first_a.description``.

``+`` is an alias for the ``namespace`` directive. So, the template above can also be written as:

::

    $ a | 0
        +       : first_a
            | text
                save: description
            | [href]
                save: url

Or, more succinctly, using inline sub-contexts and the ``:`` alias for save:

::

    $ a | 0 ; +         : first_a
            | text ;        : description
            | [href] ;      : url



Shrink Directive
^^^^^^^^^^^^^^^^

The ``shrink`` directive trims and collapses whitespace from text. It doesn't take any parameters,
so the usage is just the word ``shrink``:

::

    $ p | text ;            : with_spacing
    $ p | text ; shrink ;   : shrink_on_text

If applied to an element, it will be applied to the element's text.

::

    $ p ; shrink ;          : shrink_on_elem

Applying the above statements to the following HTML:

.. code:: html

    <p>Hello       World!</p>

Will result in the following python ``dict``:

.. code:: python

    {
        'with_spacing': 'Hello       World!',
        'shrink_on_text': 'Hello World!',
        'shrink_on_elem': 'Hello World!'
    }

Def Directive
^^^^^^^^^^^^^

The ``def`` directive saves a sub-context as a custom directive which can be invoked later. This is a
way to re-use sections of a take template. Directives created in this fashion **always result in a new**
``dict``.

The syntax is:

::

    def: <identifier>
        <sub-context>

For example:

::

    def: get first link
        $ a | 0
            | text ;    : description
            | [href] ;  : url

In the above template, a new directive named ``get first link`` is created. The new directive saves
the text and href attribute from the first ``<a>`` element in the context onto which it is
invoked. The directive will always result in a new ``dict`` containing ``description`` and
``url`` keys.

The identifier can contain spaces; all spaces are collapsed to be a single space,
e.g. ``def: some    name`` is collapsed to ``def: some name``.

Directives created by ``def`` are invoked without parameters.

The example below defines a custom directive and applies it against the first ``<nav>`` element and the first ``<aside>`` element.

::

    def: get first link
        $ a | 0
            | text ;    : description
            | [href] ;  : url

    $ nav
        get first link
            save: first_nav_link
    $ aside
        get first link
            save: first_aside_link

Given the following HTML:

.. code:: html

    <div>
        <nav>
            <a href="/local/a">nav item A</a>
            <a href="/local/b">nav item B</a>
        </nav>
        <aside>
            <p>some description</p>
            <a href="http://ext.com/a">aside item A</a>
            <a href="http://ext.com/b">aside item B</a>
        </aside>
    </div>



The template would result in:

.. code:: python

    {
        'first_nav_link': {
            'description': 'nav item A',
            'url': '/local/a'
        },
        'first_aside_link': {
            'description': 'aside item A',
            'url': 'http://ext.com/a'
        }
    }

Each time the directive is invoked it returns a python ``dict`` containing ``'description'`` and ``'url'`` keys. The return value of the first invocation is saved into the template's result as ``'first_nav_link'``. The second return value is saved as ``'first_aside_link'``

Another way to save the data from a custom directive is to use the ``| .property`` query. This allows renaming, too:

::

    def: get first link
        $ a | 0
            | text ;    : description
            | [href] ;  : url

    $ nav
        get first link
            | .url ;
                save: first_nav_url
    $ aside
        get first link
            | .url ;
                save: first_aside_url

The above template would result in the following ``dict``:

.. code:: python

    {
        'first_nav_url': '/local/a',
        'first_aside_url': 'http://ext.com/a'
    }

Merge Directive
^^^^^^^^^^^^^^^

*Alias:* ``>>``

The ``merge`` directive copies properties from the context's value and saves them into the result value. The main
use-case is extracting data from the result of a custom directive. ``merge`` performs a shallow copy.

The syntax is:

::

    merge: <field> [<field>]*

The parameter(s) are the keys to copy. They are separated by spaces or a comma and new line.

The special parameter ``*`` can be used to copy all the keys. If used, it should be the only parameter:

::

    merge: *

*Note:* ``merge`` expects the context's value to be a ``dict``; behind the scenes it uses the ``mapping[key]`` syntax.

An example:

::

    def: link info
        | text              : text
        | [href]            : url
        | [title]           : title

    $ footer a
        save each               : footer_links
            link info
                merge               : url

Applying the above take template to the following HTML:

.. code:: html

    <html>
        <head>...</head>
        <body>
            <div class="main">
                ...
            </div>
            <footer>
                <ul>
                    <li>
                        <a href="/about" title="All about our company">Team</a>
                    </li>
                    <li>
                        <a href="https://blog.example.com" title="Our self-promos">Blog</a>
                    </li>
                    <li>
                        <a href="www.facebook.com/example" title="Our facebook page">Facebook</a>
                    </li>
                    <li>
                        <a href="/privacy" title="Legalese">Privacy</a>
                    </li>
                </ul>
            </footer>
        </body>
    </html>

Will result in the following python ``dict``:

.. code:: python

    {
        'footer_links': [
            {'url': '/about'},
            {'url': 'https://blog.example.com'},
            {'url': 'www.facebook.com/example'},
            {'url': '/privacy'}
        ]
    }

To copy more than one property, separate the property names with a space or a comma and new-line:

::

                        # separated by spaces
    merge               : url title

                        # separated with comma line-continuation
    merge               : url,
                          title

                        # using the `>>` alias
    >>                  : url,
                          title


.. _PyQuery: https://pythonhosted.org/pyquery/index.html
.. _PyQuery constructor: https://pythonhosted.org/pyquery/index.html#quickstart
.. _bugs: https://github.com/gawel/pyquery/issues
.. _lxml: http://lxml.de/
.. _cssselect: https://pythonhosted.org/cssselect/
