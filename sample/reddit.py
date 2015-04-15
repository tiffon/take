from __future__ import print_function
import sys

from take import TakeTemplate


REDDIT_URL = 'http://www.reddit.com/'
TMPL_PATH = 'reddit.take'
INLINE_TMPL_PATH = 'reddit_inline_saves.take'


def get_reddit():
    tt = TakeTemplate.from_file(TMPL_PATH, base_url=REDDIT_URL)
    inline_tt = TakeTemplate.from_file(INLINE_TMPL_PATH, base_url=REDDIT_URL)
    return tt(url=REDDIT_URL), inline_tt(url=REDDIT_URL)


if __name__ == '__main__':
    try:
        import simplejson as json
    except ImportError:
        import json
    data, inline_data = get_reddit()
    print('Results of both templates are identical:', data == inline_data)
    assert data == inline_data
    print('Total reddit entries:', len(data['entries']))
    print('Printing the first entry:')
    print(json.dumps(data['entries'][0], indent=4))
