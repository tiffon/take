from __future__ import print_function

from take import TakeTemplate


REDDIT_URL = 'http://www.reddit.com/'


def get_reddit(tmpl_path='reddit.take'):
    tt = TakeTemplate.from_file(tmpl_path)
    return tt, tt(url=REDDIT_URL, base_url=REDDIT_URL)


if __name__ == '__main__':
    try:
        import simplejson as json
    except ImportError:
        import json
    _, data = get_reddit()
    print('Total reddit entries:', len(data['entries']))
    print('Printing the first two:')
    print(json.dumps(data['entries'][0:2], indent=4))
