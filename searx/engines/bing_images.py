"""
 Bing (Images)

 @website     https://www.bing.com/images
 @provide-api yes (http://datamarket.azure.com/dataset/bing/search),
              max. 5000 query/month

 @using-api   no (because of query limit)
 @results     HTML (using search portal)
 @stable      no (HTML can change)
 @parse       url, title, img_src

 @todo        currently there are up to 35 images receive per page,
              because bing does not parse count=10.
              limited response to 10 images
"""

from lxml import html
from json import loads
import re
from searx.url_utils import urlencode
from searx.utils import match_language

# engine dependent config
categories = ['images']
paging = True
safesearch = True
time_range_support = True
language_support = True
supported_languages_url = 'https://www.bing.com/account/general'

# search-url
base_url = 'https://www.bing.com/'
search_string = 'images/search?{query}&count=10&first={offset}'
time_range_string = '&qft=+filterui:age-lt{interval}'
time_range_dict = {'day': '1440',
                   'week': '10080',
                   'month': '43200',
                   'year': '525600'}

# safesearch definitions
safesearch_types = {2: 'STRICT',
                    1: 'DEMOTE',
                    0: 'OFF'}


_quote_keys_regex = re.compile('({|,)([a-z][a-z0-9]*):(")', re.I | re.U)


# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * 10 + 1

    search_path = search_string.format(
        query=urlencode({'q': query}),
        offset=offset)

    language = match_language(params['language'], supported_languages).lower()

    params['cookies']['SRCHHPGUSR'] = \
        'ADLT=' + safesearch_types.get(params['safesearch'], 'DEMOTE')

    params['cookies']['_EDGE_S'] = 'mkt=' + language +\
        '&ui=' + language + '&F=1'

    params['url'] = base_url + search_path
    if params['time_range'] in time_range_dict:
        params['url'] += time_range_string.format(interval=time_range_dict[params['time_range']])

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    # parse results
    for result in dom.xpath('//div[@id="mmComponent_images_1"]/ul/li/div/div[@class="imgpt"]'):
        link = result.xpath('./a')[0]

        # TODO find actual title
        title = link.xpath('.//img/@alt')[0]

        # parse json-data (it is required to add a space, to make it parsable)
        json_data = loads(_quote_keys_regex.sub(r'\1"\2": \3', link.attrib.get('m')))

        url = json_data.get('purl')
        img_src = json_data.get('murl')
        thumbnail = json_data.get('turl')

        # append result
        results.append({'template': 'images.html',
                        'url': url,
                        'title': title,
                        'content': '',
                        'thumbnail_src': thumbnail,
                        'img_src': img_src})

        # TODO stop parsing if 10 images are found
        # if len(results) >= 10:
        #     break

    # return results
    return results


# get supported languages from their site
def _fetch_supported_languages(resp):
    supported_languages = []
    dom = html.fromstring(resp.text)

    regions_xpath = '//div[@id="region-section-content"]' \
                    + '//ul[@class="b_vList"]/li/a/@href'

    regions = dom.xpath(regions_xpath)
    for region in regions:
        code = re.search('setmkt=[^\&]+', region).group()[7:]
        if code == 'nb-NO':
            code = 'no-NO'

        supported_languages.append(code)

    return supported_languages
