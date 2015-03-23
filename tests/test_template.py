import pytest

from take import TakeTemplate
from take.parser import UnexpectedTokenError, InvalidDirectiveError
from take.scanner import ScanError

HTML_FIXTURE = """
<div>
    <h1 id="id-on-h1">Text in h1</h1>
    <nav>
        <ul id="first-ul" title="nav ul title">
            <li>
                <a href="/local/a">first nav item</a>
            </li>
            <li>
                <a href="/local/b">second nav item</a>
            </li>
        </ul>
    </nav>
    <section>
        <p>some description</p>
        <ul id="second-ul" title="content ul title">
            <li>
                <a href="http://ext.com/a">first content link</a>
            </li>
            <li>
                <a href="http://ext.com/b">second content link</a>
            </li>
        </ul>
    </section>
</div>
"""

def test_template_compiles():
    TMPL = """
        $ h1 | text
            save: value
    """
    tt = TakeTemplate(TMPL)
    assert tt


def test_css_text():
    TMPL = """
        $ h1 | text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': 'Text in h1'}


def test_index():
    TMPL = """
        $ a | 0 text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': 'first nav item'}


def test_absent_index():
    TMPL = """
        $ i | 0 text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': ''}


def test_neg_index():
    TMPL = """
        $ a | -1 text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': 'second content link'}


def test_absent_neg_index():
    TMPL = """
        $ i | -1 text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': ''}


def test_deep_save():
    TMPL = """
        $ h1 | text
            save: deep.value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'deep': {'value': 'Text in h1'}}


def test_sub_ctx():
    TMPL = """
        $ section
            $ ul | [id]
                save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': 'second-ul'}


def test_sub_ctx_empty():
    TMPL = """
        $ nav
            $ ul | 1 [id]
                save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'value': None}


def test_exit_sub_ctx():
    TMPL = """
        $ nav
            $ ul | 0 [id]
                save: sub_ctx_value
        $ p | text
            save: value
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'sub_ctx_value': 'first-ul',
                    'value': 'some description'}


def test_comments():
    TMPL = """
        # shouldn't affect things
        $ nav
            # shouldn't affect things
            $ ul | 0 [id]
            # shouldn't affect things
        # shouldn't affect things
                save: sub_ctx_value
        # shouldn't affect things
        $ p | text
        # shouldn't affect things
            save: value
            # shouldn't affect things
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'sub_ctx_value': 'first-ul',
                    'value': 'some description'}


def test_save_each():
    TMPL = """
        $ nav
            $ a
                save each: nav
                    | [href]
                        save: url
                    | text
                        save: text
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    expect = {
        'nav': [{
                'url': '/local/a',
                'text': 'first nav item'
            },{
                'url': '/local/b',
                'text': 'second nav item'
            }
        ]
    }
    assert data == expect


def test_deep_save_each():
    TMPL = """
        $ nav
            $ a
                save each: nav.items
                    | [href]
                        save: item.url
                    | text
                        save: item.text
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    expect = {
        'nav': {
            'items': [{
                    'item': {
                        'url': '/local/a',
                        'text': 'first nav item'
                    }
                },{
                    'item': {
                        'url': '/local/b',
                        'text': 'second nav item'
                    }
                }
            ]
        }
    }
    assert data == expect


def test_base_url():
    TMPL = """
        $ a | 0 [href]
            save: local
        $ a | -1 [href]
            save: ext
    """
    tt = TakeTemplate(TMPL)
    data = tt(HTML_FIXTURE)
    assert data == {'local': '/local/a',
                    'ext': 'http://ext.com/b'}
    data = tt(HTML_FIXTURE, base_url='http://www.example.com')
    assert data == {'local': 'http://www.example.com/local/a',
                    'ext': 'http://ext.com/b'}


def test_invalid_directive_statement_error():
    TMPL = """
        $ h1 | [href]
            save fail
    """
    with pytest.raises(ScanError):
        tt = TakeTemplate(TMPL)


def test_invalid_directive_id_error():
    TMPL = """
        $ h1 | [href]
            hm: fail
    """
    with pytest.raises(InvalidDirectiveError):
        tt = TakeTemplate(TMPL)


def test_invalid_query_error():
    TMPL = """
        .hm | [href]
            hm: fail
    """
    with pytest.raises(ScanError):
        tt = TakeTemplate(TMPL)


def test_attr_text_error():
    TMPL = """
        $ h1 | [href] text
            save: fail
    """
    with pytest.raises(UnexpectedTokenError):
        tt = TakeTemplate(TMPL)
