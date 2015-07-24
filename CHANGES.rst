Take Changelog
==============

Here you can see the full list of changes between each take release.


Version 0.2.1
-------------

Release Pending.

- Support intra-line hard-tabs.


Version 0.2.0
-------------

Released April 15 2015.

- Added the "def" directive to define sub-routines.
- Added the "namespace" directive, with "+" alias.
- Added the "merge" directive, with alias ">>".
- Added the field accessor.
- Added the "own_text" accessor.
- Added the "shrink" directive.
- Added comma line-continuations in directive parameter lists.
- Inline sub-contexts changed to support sub-contexts of their own (instead of having the max-depth).
- The sample now compares the results of "reddit.take" vs "reddit_inline_saves.take" instead of only using one of them.
- "reddit_inline_saves.take" changed to use namespaces.

- Allow directives that don't require parameters.
- Directives also end on ";".
- Remove underscores on `ContextParser` method names that are used by directives.
- Created a ``DirectiveStatementEnd`` token type.
- Directives are now looked up by name and are external functions with a defined signature.
- Adjusted the scanner to accept a wider range of directive names.


Version 0.1.0
-------------

Released on April 6 2015.

- Inline sub-contexts added.
- Added ``:`` as an alias for ``save:``.
- ``TakeTemplate.from_file()`` static method accepts ``base_url`` parameter.
- Tests slightly reorganized.
- Additional tests added.


Version 0.0.6
-------------

Released on April 6 2015.

- Link to reddit sample fixed in README.


Version 0.0.5
-------------

Released on April 6 2015.

- ``TakeTemplate.from_file()`` static method added.
- README.rst updated to include ``TakeTemplate.from_file()``.
- Moved the reddit sample out of the package code.
- Minor misc cleanup.


Version 0.0.4
-------------

Released on March 27 2015.

- Links and installation instructions added to readme.
- Minor misc cleanup.
- Added test for an invalid save-each directive.
- Better error formatting.
- Copyright in LICENSE changed to "Joe Farro" instead of "tiffon".
- CHANGES.rst file added to sources.
- AUTHORS.rst file added to sources.


Version 0.0.3
-------------

Released on March 25 2015.

- PyPi long description read from README.rst.
- Support added for Python 3.3.
- Tox configured for py 26, 27, 33, and pypy.
- Readme fix.


Version 0.0.2
-------------

Released on March 25 2015.

- Readme update.


Version 0.0.1
-------------

Released on March 25 2015.

- Readme update.


Version 0.0.0
-------------

Released on March 25 2015.

First public release.
