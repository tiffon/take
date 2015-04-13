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


    def test_sub_ctx(self):
        TMPL = """
            $ section
                $ ul | [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'value': 'second-ul'}


    def test_sub_ctx_empty(self):
        TMPL = """
            $ nav
                $ ul | 1 [id]
                    save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
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


    def test_accessor_sub_ctx_save(self):
        TMPL = """
            $ h1
                | 0 text ; save: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


    def test_css_accessor_sub_ctx_save_alias(self):
        TMPL = """
            $ h1 | 0 text ; : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'Text in h1'


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
