from __future__ import print_function
import sys

from take import TakeTemplate


REDDIT_URL = 'http://www.reddit.com/'
TMPL_PATH = 'reddit.take'
INLINE_TMPL_PATH = 'reddit_inline_saves.take'


def get_reddit(tmpl_path):
    tt = TakeTemplate.from_file(tmpl_path, base_url=REDDIT_URL)
    return tt, tt(url=REDDIT_URL)


if __name__ == '__main__':
    try:
        import simplejson as json
    except ImportError:
        import json
    if 'inline' in sys.argv:
        tmpl_path = INLINE_TMPL_PATH
    else:
        tmpl_path = TMPL_PATH
    print('Using template: ', tmpl_path)
    _, data = get_reddit(tmpl_path)
    print('Total reddit entries:', len(data['entries']))
    print('Printing the first two:')
    data['entries'] = data['entries'][0:2]
    print(json.dumps(data, indent=4))
