from pyquery import PyQuery

import parser


class TakeTemplate(object):

    def __init__(self, src):
        self.node = parser.parse(src)

    def take(self, *args, **kwargs):
        base_url = kwargs.pop('base_url', None)
        _doc = PyQuery(*args, **kwargs)
        if base_url:
            _doc.make_links_absolute(base_url)
        rv = {}
        self.node.do(None, rv=rv, value=_doc, last_value=_doc)
        return rv

    def __call__(self, *args, **kwargs):
        return self.take(*args, **kwargs)


TEST_HTML = """
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
"""

TEST_TMPL = """
    $ h1 | text
        save: h1_title
    $ p | 1 text
        save: p_text
    $ #a li
        | 0 [title]
            save: a.first_li
        | 1 text
            save: a.second_li
    $ #b li
        | 0 [title]
            save: b.first_li
        | 1 text
            save: b.second_li

"""

SE_TMPL = """
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

"""

SE_TMPL_2 = """
    # the h1 thing
    $ h1 | text
        save: h1_title
    # grab the <li> items
    $ li
        save each: li_data
            | [title]
                save: title
            | text
                save: text
    $ p | 1 text
        save: p_text

"""
