import pytest

from pyquery import PyQuery

from take import TakeTemplate
from take.parser import InvalidDirectiveError, UnexpectedTokenError, TakeSyntaxError
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

DOC = PyQuery(HTML_FIXTURE)


@pytest.mark.basic
class TestBaseFunctionality():

    def test_template_compiles(self):
        TMPL = """
            $ h1 | text
                save: value
        """
        tt = TakeTemplate(TMPL)
        assert tt


    def test_save(self):
        TMPL = """
            save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'].html() == DOC.html()


    def test_save_alias(self):
        TMPL = """
            : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'].html() == DOC.html()


    def test_deep_save(self):
        TMPL = """
            save: parent.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['parent']['value'].html() == DOC.html()


    def test_deep_save_alias(self):
        TMPL = """
            : parent.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['parent']['value'].html() == DOC.html()


    def test_save_css_query(self):
        TMPL = """
            $ h1
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'].html() == DOC('h1').html()


    def test_save_css_text_query(self):
        TMPL = """
            $ h1 | text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data == {'value': 'Text in h1'}


    def test_save_css_index_query(self):
        TMPL = """
            $ a | 0
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'].html() == DOC('a').eq(0).html()


    def test_save_css_index_text_query(self):
        TMPL = """
            $ a | 0 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == 'first nav item'


    def test_absent_index(self):
        TMPL = """
            $ notpresent | 0 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == ''


    def test_neg_index(self):
        TMPL = """
            $ a | -1 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == 'second content link'


    def test_absent_neg_index(self):
        TMPL = """
            $ notpresent | -1 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == ''


    def test_query_deep_save(self):
        TMPL = """
            $ h1 | text
                save: deep.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data == {'deep': {'value': 'Text in h1'}}


    def test_sub_ctx(self):
        TMPL = """
            $ section
                $ ul | [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data == {'value': 'second-ul'}


    def test_sub_ctx_empty(self):
        TMPL = """
            $ nav
                $ ul | 1 [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data == {'value': None}


    def test_exit_sub_ctx(self):
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


    def test_comments(self):
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


    def test_save_each(self):
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


    def test_deep_save_each(self):
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


    def test_base_url(self):
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


    def test_base_url_on_tmpl(self):
        TMPL = """
            $ a | 0 [href]
                save: local
            $ a | -1 [href]
                save: ext
        """
        tt = TakeTemplate(TMPL, base_url='http://www.example.com')
        data = tt(HTML_FIXTURE)
        assert data == {'local': 'http://www.example.com/local/a',
                        'ext': 'http://ext.com/b'}


@pytest.mark.inline_ctx
class TestInlineSubCtx():

    def test_css_sub_ctx_save(self):
        TMPL = """
            $ h1 | 0 text ; save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == 'Text in h1'

    def test_accessor_sub_ctx_save(self):
        TMPL = """
            $ h1
                | 0 text ; save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == 'Text in h1'

    def test_css_accessor_sub_ctx_save_alias(self):
        TMPL = """
            $ h1 | 0 text ; : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['value'] == 'Text in h1'


@pytest.mark.namespace_ctx
class TestNamespaceCtx():

    def test_save_text(self):
        TMPL = """
            namespace               : parent
                $ h1 | 0 text ;         : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        value = DOC('h1').text()
        assert data['parent']['value'] == 'Text in h1'

    def test_alias_save_text(self):
        TMPL = """
            +                       : parent
                $ h1 | 0 text ;         : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        value = DOC('h1').text()
        assert data['parent']['value'] == 'Text in h1'

    def test_namespace_inception(self):
        TMPL = """
            +                       : p0
                +                       : p1
                    +                       : p2
                        +                       : p3
                            +                       : p4
                                $ h1 | 0 text ;         : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        value = DOC('h1').text()
        assert data['p0']['p1']['p2']['p3']['p4']['value'] == 'Text in h1'

    def test_namespace_exits(self):
        TMPL = """
            +                               : p0a
                namespace                       : p1a
                    $ li | 0 text ;                 : first_li
                +                               : p1b
                    $ li | 1 text ;                 : second_li
            namespace                       : p0b
                $ li | 2 text ;                 : third_li
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['p0a']['p1a']['first_li'] == 'first nav item'
        assert data['p0a']['p1b']['second_li'] == 'second nav item'
        assert data['p0b']['third_li'] == 'first content link'

    def test_inline_namespace(self):
        TMPL = """
            $ li ; +                            : parent
                | 0 text ;                          : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['parent']['value'] == 'first nav item'

    def test_inline_namespace_exits_and_sub_ctx(self):
        TMPL = """
            $ li ; +                        : p0a
                | 0 ; +                         : p1a
                    | text ;                        : first_li
                | 1 text ;                      : second_li
            +                               : p0b
                $ h1 | 0 text ; +               : p1b
                                                    : h1
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['p0a']['p1a']['first_li'] == 'first nav item'
        assert data['p0a']['second_li'] == 'second nav item'
        assert data['p0b']['p1b']['h1'] == 'Text in h1'

    def test_inline_namespace_minimal_indentation(self):
        TMPL = """
            $ li ; +                        : p0a
             | 0 ; +                            : p1a
              | text ;                              : first_li
             | 1 text ;                         : second_li
             | 1 text ;                         : second_li_again
            +                               : p0b
             $ h1 | 0 text ; +                  : p1b
                                                    : h1
        """
        tt = TakeTemplate(TMPL)
        data = tt(HTML_FIXTURE)
        assert data['p0a']['p1a']['first_li'] == 'first nav item'
        assert data['p0a']['second_li'] == 'second nav item'
        assert data['p0a']['second_li_again'] == 'second nav item'
        assert data['p0b']['p1b']['h1'] == 'Text in h1'


@pytest.mark.invalid_templates
class TestInvalidTemplates():

    def test_invalid_directive_statement_error(self):
        TMPL = """
            $ h1 | [href]
                save fail
        """
        with pytest.raises(ScanError):
            tt = TakeTemplate(TMPL)


    def test_invalid_directive_id_error(self):
        TMPL = """
            $ h1 | [href]
                hm: fail
        """
        with pytest.raises(InvalidDirectiveError):
            tt = TakeTemplate(TMPL)


    def test_invalid_query_error(self):
        TMPL = """
            .hm | [href]
                hm: fail
        """
        with pytest.raises(ScanError):
            tt = TakeTemplate(TMPL)


    def test_attr_text_error(self):
        TMPL = """
            $ h1 | [href] text
                save: fail
        """
        with pytest.raises(UnexpectedTokenError):
            tt = TakeTemplate(TMPL)


    def test_invalid_save_each_context(self):
        TMPL = """
            $ li
                save each: items
            $ h1
                save: fail
        """
        with pytest.raises(TakeSyntaxError):
            tt = TakeTemplate(TMPL)
