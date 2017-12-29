
# coding: utf-8

# In[ ]:

import requests
from lxml.html import fromstring
from lxml import cssselect


# In[ ]:

url_template = 'http://and-rus.ru/service/{}_{}/'
urls = []
for author in ['calibrpressuread', 'termometrcalibration']:
    for page in range(1,200):
        urls.append(url_template.format(author, page))
        
flatten = lambda l: [item for sublist in l for item in sublist]


# In[ ]:

text = ''
for url in urls:
    try:
        html = requests.get(url).text
        dom = fromstring(html)
        dom.make_links_absolute(url)
        css_elements = flatten (dom.cssselect('.article'))
        text += "\n".join([t.text_content().strip() +';' + t.get('href').strip() for t in css_elements])
        if css_elements != []:
            text += '\n'
    except AttributeError:
        pass
with open('doclist.csv', 'w', encoding='utf-8') as f:
    f.write(text)

