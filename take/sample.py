from take_template import TakeTemplate


REDDIT_URL = 'http://www.reddit.com/'

REDDIT_TMPL = """
$ #siteTable .thing
    save each: entries
        $ .rank | text
            save: rank
        $ .score.unvoted | text
            save: score
        $ a.title | text
            save: title
        $ .domain a
            | text
                save: domain.text
            | [href]
                save: domain.reddit_section
        $ .tagline
            $ time
                | [datetime]
                    save: time.exact
                | text
                    save: time.desc
            $ .author
                | [href]
                    save: author.url
                | text
                    save: author.login
            $ .subreddit
                | [href]
                    save: section.url
                | text
                    save: section.name
        $ .comments | text
            save: num_comments
"""

def get_reddit():
    tt = TakeTemplate(REDDIT_TMPL)
    return tt, tt(url=REDDIT_URL, base_url=REDDIT_URL)

if __name__ == '__main__':
    try:
        import simplejson as json
    except ImportError:
        import json
    _, data = get_reddit()
    print 'Total reddit entries:', len(data['entries'])
    print 'Printing the first two:'
    print json.dumps(data['entries'][0:2], indent=4)
