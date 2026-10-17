from requests import get
from bs4 import BeautifulSoup as bs4


class Object:
    def __init__(self):
        self.referenced_from = []
        self.appears_in = []
        self.name = ''
        self.fields = []
        '''(name, format, desc)'''
    def __str__(self):
        return f"""@Type
class {self.name}(Obj):
    '''
    appears in {self.appears_in}
    referenced from {self.referenced_from}
    '''
    """ + '\n    '.join(
            name + ' = ' + format + f"\n    '''{desc}'''" for name, format, desc in self.fields
        )

r = get('https://source.android.com/docs/core/runtime/dex-format')
soup = bs4(r.text)

docs = soup.find('div', class_ = 'devsite-article-body clearfix')

objs=[]
obj=Object()
for i in docs:
    if i['name'] == 'h3':
        objs.append(obj)
        obj = Object()
        obj.name = i['data-text']
    if i['name'] == 'h4' and i['data-text'].startswith('Appears in the '):
        obj.appears_in.append(i['data-text'][15:])
    if i['name'] == 'h4' and i['data-text'].startswith('Referenced from '):
        obj.referenced_from.append(i['data-text'][16:])
    if