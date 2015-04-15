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


@pytest.mark.directives
@pytest.mark.namespace_directive
class TestNamespaceCtx():

    def test_save_text(self):
        TMPL = """
            namespace               : parent
                $ h1 | 0 text ;         : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        value = pq_doc('h1').text()
        assert data['parent']['value'] == 'Text in h1'


    def test_alias_save_text(self):
        TMPL = """
            +                       : parent
                $ h1 | 0 text ;         : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        value = pq_doc('h1').text()
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
        data = tt(html_fixture)
        value = pq_doc('h1').text()
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
        data = tt(html_fixture)
        assert data['p0a']['p1a']['first_li'] == 'first nav item'
        assert data['p0a']['p1b']['second_li'] == 'second nav item'
        assert data['p0b']['third_li'] == 'first content link'


    def test_inline_namespace(self):
        TMPL = """
            $ li ; +                            : parent
                | 0 text ;                          : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
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
        data = tt(html_fixture)
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
        data = tt(html_fixture)
        assert data['p0a']['p1a']['first_li'] == 'first nav item'
        assert data['p0a']['second_li'] == 'second nav item'
        assert data['p0a']['second_li_again'] == 'second nav item'
        assert data['p0b']['p1b']['h1'] == 'Text in h1'


@pytest.mark.directives
@pytest.mark.def_directive
class TestDefDirective():

    def test_basic_def(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: def_saved
            simple
                save: def_result
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['def_result']['def_saved'] == 'Text in h1'


    def test_def_inline_sub(self):
        TMPL = """
            def: simple
                $ h1 | 0 text
                    save: def_saved

            simple ; save: def_result
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['def_result']['def_saved'] == 'Text in h1'


    def test_def_space_in_name(self):
        TMPL = """
            def: my simple defn
                $ h1 | 0 text
                    save: def_saved

            my simple defn ; save: def_result
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['def_result']['def_saved'] == 'Text in h1'


    def test_def_save_each(self):
        expect = {
            'first': {
                'items': [
                    {'url': '/local/a',
                     'desc': 'first nav item'},
                    {'url': '/local/b',
                     'desc': 'second nav item'}
                ]
            },
            'second': {
                'items': [
                    {'url': 'http://ext.com/a',
                     'desc': 'first content link'},
                    {'url': 'http://ext.com/b',
                     'desc': 'second content link'}
                ]
            }
        }
        TMPL = """
            def: simple
                $ li a
                    save each               : items
                        | [href] ;              : url
                        | text ;                : desc

            $ #first-ul
                simple ;                : first
            $ #second-ul
                simple ;                : second
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == expect
        TMPL = """
            def: simple
                $ li a
                    save each               : items
                        | [href] ;              : url
                        | text ;                : desc

            $ #first-ul ; simple ;      : first
            $ #second-ul ; simple ;     : second
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == expect


    def test_def_child_scoping(self):
        TMPL = """
            $ h1
                def: simple
                    $ h1 | 0 text
                        save: def_saved

            simple ; save: simple_should_error
        """
        with pytest.raises(InvalidDirectiveError):
            tt = TakeTemplate(TMPL)


    def test_def_shadowing(self):
        TMPL = """

            def: simple
                $ li | 0 text
                    save: value
            $ ul
                def: simple
                    $ li | 1 text
                        save: value
                simple ;                    : shadowed
            simple ;                        : parent_scope
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'parent_scope': {
                'value': 'first nav item'
            },
            'shadowed': {
                'value': 'second nav item'
            }
        }
        assert data == expect


@pytest.mark.directives
@pytest.mark.merge_directive
class TestMergeDirective():

    def test_basic_merge(self):
        TMPL = """
            def: simple
                $ li | 0 text
                        save: value
            simple
                merge: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'first nav item'

    def test_merge_alias(self):
        TMPL = """
            def: simple
                $ li | 0 text
                        save: value
            simple
                >> : value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'first nav item'


    def test_basic_merge_all(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: zero_tx
                    | 1 text
                        save: one_tx
            simple
                merge: *
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['zero_tx'] == 'first nav item'
        assert data['one_tx'] == 'second nav item'


    def test_deep_merge_all(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: item.zero_tx
                    | 1 text
                        save: item.one_tx
            simple
                merge: *
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['item']['zero_tx'] == 'first nav item'
        assert data['item']['one_tx'] == 'second nav item'


    def test_merge_only_prop(self):
        TMPL = """
            def: simple
                $ li | 0 text
                    save: value
            simple
                merge: value
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['value'] == 'first nav item'


    def test_merge_one_prop_from_multiple(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: zero_tx
                    | 1 text
                        save: one_tx
            simple
                merge: zero_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'zero_tx': 'first nav item'}


    def test_merge_one_deep_prop(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: item.zero_tx
                    | 1 text
                        save: item.one_tx
            simple
                merge: item.zero_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data == {'item': {'zero_tx': 'first nav item'}}


    def test_merge_two_props(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: zero_tx
                    | 1 text
                        save: one_tx
            simple
                merge: zero_tx one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'zero_tx': 'first nav item',
            'one_tx': 'second nav item'
        }
        assert data == expect


    def test_merge_two_deep_props(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: item.zero_tx
                    | 1 text
                        save: item.one_tx

            simple ; >> : item.zero_tx item.one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'item': {
                'zero_tx': 'first nav item',
                'one_tx': 'second nav item'
            }
        }
        assert data == expect


    def test_merge_deep_and_shallow(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text
                        save: zero_tx
                    | 1 text
                        save: item.one_tx
            simple
                merge: zero_tx item.one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'zero_tx': 'first nav item',
            'item': {
                'one_tx': 'second nav item'
            }
        }
        assert data == expect


    def test_merge_line_continuation(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text ;      : zero_tx
                    | 1 text ;      : one_tx
            simple
                merge               : zero_tx,
                                      one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'zero_tx': 'first nav item',
            'one_tx': 'second nav item'
        }
        assert data == expect


    def test_merge_line_continuation_w_space(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text ;      : zero_tx
                    | 1 text ;      : one_tx
            simple
                merge               : zero_tx      ,
                                      one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'zero_tx': 'first nav item',
            'one_tx': 'second nav item'
        }
        assert data == expect


    def test_deep_merge_line_continuation(self):
        TMPL = """
            def: simple
                $ li
                    | 0 text ;      : item.zero_tx
                    | 1 text ;      : item.one_tx
            simple
                merge               : item.zero_tx,
                                      item.one_tx
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        expect = {
            'item': {
                'zero_tx': 'first nav item',
                'one_tx': 'second nav item'
            }
        }
        assert data == expect


@pytest.mark.directives
@pytest.mark.shrink_directive
class TestShrinkDirective():

    def test_basic_shrink(self):
        TMPL = """
            $ #text-with-newlines
                | text ;                    save: article
                | text ; shrink ;           save: article_shrunk
                | own_text ;                save: article_own
                | own_text ; shrink ;       save: article_own_shrunk
                $ em
                    | text ;                save: em
                    | text ; shrink ;       save: em_shrunk
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['article'] != 'articles multiline text with a child em more article text'
        assert data['article_shrunk'] == 'articles multiline text with a child em more article text'
        assert data['article_own'] != 'articles multiline text more article text'
        assert data['article_own_shrunk'] == 'articles multiline text more article text'
        assert data['em'] != 'with a child em'
        assert data['em_shrunk'] == 'with a child em'


    def test_auto_call_text(self):
        TMPL = """
            $ #text-with-newlines em
                | text ;                    save: em
                | text ; shrink ;           save: em_shrunk
                shrink ;                    save: auto_texted
        """
        tt = TakeTemplate(TMPL)
        data = tt(html_fixture)
        assert data['em'] != 'with a child em'
        assert data['em_shrunk'] == 'with a child em'
        assert data['auto_texted'] == 'with a child em'
