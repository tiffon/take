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
