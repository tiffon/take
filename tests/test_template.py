import os
import pytest

from pyquery import PyQuery

from take import TakeTemplate
from take.parser import InvalidDirectiveError, UnexpectedTokenError, TakeSyntaxError
from take.scanner import ScanError

here = os.path.dirname(os.path.abspath(__file__))
with open(here + '/doc.html') as f:
    html_fixture = f.read()

pq_doc = PyQuery(html_fixture)


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
        data = tt(html_fixture)
        assert data['value'].html() == pq_doc.html()


    def test_save_alias(self):
        TMPL = """
            : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'].html() == pq_doc.html()


    def test_deep_save(self):
        TMPL = """
            save: parent.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['parent']['value'].html() == pq_doc.html()


    def test_deep_save_alias(self):
        TMPL = """
            : parent.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['parent']['value'].html() == pq_doc.html()


    def test_save_css_query(self):
        TMPL = """
            $ h1
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'].html() == pq_doc('h1').html()


    def test_save_css_query_hard_tabs(self):
        TMPL = """
\t\t\t$ h1
\t\t\t\tsave: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'].html() == pq_doc('h1').html()


    def test_save_css_text_query(self):
        TMPL = """
            $ h1 | text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'Text in h1'}


    def test_save_css_index_query(self):
        TMPL = """
            $ a | 0
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'].html() == pq_doc('a').eq(0).html()


    def test_save_css_index_text_query(self):
        TMPL = """
            $ a | 0 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'first nav item'


    def test_absent_index(self):
        TMPL = """
            $ notpresent | 0 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == ''


    def test_neg_index(self):
        TMPL = """
            $ a | -1 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'second content link'


    def test_absent_neg_index(self):
        TMPL = """
            $ notpresent | -1 text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == ''


    def test_query_deep_save(self):
        TMPL = """
            $ h1 | text
                save: deep.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'deep': {'value': 'Text in h1'}}


    def test_save_attr(self):
        TMPL = """
            $ h1 | [id]
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'id-on-h1'


    def test_save_absent_attr(self):
        TMPL = """
            $ h1 | [mia]
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == None


    def test_sub_ctx_save(self):
        TMPL = """
            $ section
                $ ul | [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'second-ul'}


    def test_sub_ctx_save_hard_tabs(self):
        TMPL = """
\t\t\t$ section
\t\t\t\t\t$ ul\t|\t\t[id]
\t\t\t\t\t\t\tsave: \t \tvalue
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'second-ul'}


    def test_sub_ctx_save_alias(self):
        TMPL = """
            $ section
                $ ul | [id]
                    : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'second-ul'}


    def test_sub_ctx_save_empty(self):
        TMPL = """
            $ nav
                $ ul | 1 [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': None}


    def test_sub_ctx_save_alias_empty(self):
        TMPL = """
            $ nav
                $ ul | 1 [id]
                    : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': None}


    def test_exit_sub_ctx_save(self):
        TMPL = """
            $ nav
                $ ul | 0 [id]
                    save: sub_ctx_value
            $ p | text
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'sub_ctx_value': 'first-ul',
                        'value': 'some description'}


    def test_exit_sub_ctx_save_alias(self):
        TMPL = """
            $ nav
                $ ul | 0 [id]
                    : sub_ctx_value
            $ p | text
                : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
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
        data = tt(html_fixture)
        assert data == {'sub_ctx_value': 'first-ul',
                        'value': 'some description'}


    def test_comments_id_selector(self):
        TMPL = """
            $ #id-on-h1 | [id]
                save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'id-on-h1'}


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
        data = tt(html_fixture)
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
        data = tt(html_fixture)
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
        data = tt(html_fixture)
        assert data == {'local': '/local/a',
                        'ext': 'http://ext.com/b'}
        data = tt(html_fixture, base_url='http://www.example.com')
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
        data = tt(html_fixture)
        assert data == {'local': 'http://www.example.com/local/a',
                        'ext': 'http://ext.com/b'}


@pytest.mark.invalid_templates
class TestInvalidTemplates():

    def test_invalid_directive_statement_error(self):
        TMPL = """
            $ h1 | [href]
                save fail
        """
        with pytest.raises(InvalidDirectiveError):
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
        with pytest.raises(InvalidDirectiveError):
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


@pytest.mark.inline_ctx
class TestInlineSubCtx():

    def test_css_sub_ctx_save(self):
        TMPL = """
            $ h1 | 0 text ; save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'

    def test_css_sub_ctx_save_alias_nested(self):
        TMPL = """
            $ h1 | 0 text ; : parent.value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['parent']['value'] == 'Text in h1'


    def test_accessor_sub_ctx_save(self):
        TMPL = """
            $ h1
                | 0 text ; save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_multiple_inline_sub_ctx(self):
        TMPL = """
            $ h1 ; | 0 ; | text ; : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_sub_ctx_of_inline_sub_ctx(self):
        TMPL = """
            $ h1 ; | 0 ; | text
                : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_exits_sub_ctx_of_inline_sub_ctx(self):
        TMPL = """
            $ h1 ; | 0 ; | text
                : h1_value
            $ p | text
                : p_value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['h1_value'] == 'Text in h1'
        assert data['p_value'] == 'some description'


    def test_hard_tabs_w_inline_sub_ctxs(self):
        TMPL = """
            $ h1 ;\t\t| 0 ;\t\t| text
                :\t\t\t\t\t\t\t\th1_value
            $ p | text
                :\t\t\t\t\t\t\t\tp_value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['h1_value'] == 'Text in h1'
        assert data['p_value'] == 'some description'


@pytest.mark.field_accessor
class TestFieldAccessor():

    def test_basic_field_accessor(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: def_value
            simple
                | .def_value
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_basic_field_accessor_w_hard_tabs(self):
        TMPL = """
            def: simple
                $\th1\t|\t0\ttext
                    save\t:\tdef_value
            simple
                |\t.def_value
                    save:\tvalue
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_deep_field_accessor(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: item.def_value

            simple
                save        : raw_result
            simple
                | .item.def_value
                    save    : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['raw_result']['item']['def_value'] == 'Text in h1'
        assert data['value'] == 'Text in h1'


    def test_absent_field(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: def_value

            simple
                | .not_there
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == None


    def test_deep_absent_field(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: def_value

            simple
                | .very.not_there
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == None


@pytest.mark.own_text_accessor
class TestOwnTextAccessor():

    def test_basic_own_text(self):
        TMPL = """
            $ #not-all-own-text
                | text ;        save: full_text
                | own_text ;    save: own_text
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['full_text'] == 'own text not own text more own text'
        assert data['own_text'] == 'own text  more own text'


@pytest.mark.regexp
class TestRegexpQuery():

    def test_basic_terse_regexp(self):
        TMPL = """
            $ h1 | 0 text
                `in \w+`
                    rx match
                        | 0
                            save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'in h1'


    def test_terse_regexp_capture_groups(self):
        TMPL = """
            $ h1 | 0 text
                `in (\w+)`
                    rx match
                        | 0
                            save: all_match
                        | 1
                            save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['all_match'] == 'in h1'
        assert data['value'] == 'h1'


    def test_terse_regexp_custom_accessor(self):
        TMPL = """
            accessor: in stuff
                `in (\w+)`
                    rx match
                        set context

            $ h1 | 0 text
                in stuff
                    | 0
                        save: all_match
                    | 1
                        save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['all_match'] == 'in h1'
        assert data['value'] == 'h1'


    def test_basic_verbose_regexp(self):
        TMPL = """
            $ h1 | 0 text
                ```
                    in
                    \s
                    \w+
                ```
                    rx match
                        | 0
                            save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'in h1'


    def test_verbose_url_regexp(self):
        TMPL = """
            accessor: url parts
                ```
                    (https?)
                    (://)
                    ([^/]+)
                    (?:/(.+))?
                ```
                    set context

            $ #second-ul a
                save each                   : urls
                    | [href]
                        url parts
                            rx match
                                | 1 ;           : protocol
                                | 3 ;           : domain
                                | 4 ;           : page
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = [
            {
                'protocol': 'http',
                'domain': 'ext.com',
                'page': 'a'
            },
            {
                'protocol': 'http',
                'domain': 'ext.com',
                'page': 'b'
            }
        ]
        assert data['urls'] == expect
