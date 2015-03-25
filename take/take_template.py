from pyquery import PyQuery

from .parser import parse


class TakeTemplate(object):

    def __init__(self, src, **kwargs):
        self.node = parse(src)
        self.base_url = kwargs.get('base_url', None)

    def take(self, *args, **kwargs):
        base_url = kwargs.pop('base_url', None) or self.base_url
        _doc = PyQuery(*args, **kwargs)
        if base_url:
            _doc.make_links_absolute(base_url)
        rv = {}
        self.node.do(None, rv=rv, value=_doc, last_value=_doc)
        return rv

    def __call__(self, *args, **kwargs):
        return self.take(*args, **kwargs)
