# coding=utf8
import sys
import bs4
import urllib
import requests

from contextlib import contextmanager

def readfile(filename):
    fd = open(filename)
    retList=[]
    line = fd.readline()
    while line:
        line = line.strip('\n')
        if len(line) > 5:
            retList.append(line)
        line = fd.readline()
    fd.close()
    retList.sort()
    return retList

class Spider(object):
    def __init__(self, lang='eng', timeout=3):
        self.html_url = "http://dict.youdao.com/w/{}/".format(lang)
        self.timeout = timeout

    @contextmanager
    def soup(self, target_word):
        url = self.html_url + urllib.quote(target_word.replace('/', ''))
        try:
            req = requests.get(url, timeout=self.timeout)
        except requests.Timeout:
            sys.stderr.write('link `{}` timeout\r\n'.format(url))
            exit(1)
        except requests.ConnectionError:
            sys.stderr.write('link `{}` failed\r\n'.format(url))
            exit(1)
        except Exception:
            sys.stderr.write('link `{}` unknown error\r\n')
            exit(1)

        if not req.status_code == 200:
            sys.stderr.write('link `{}` invalid err: {}\r\n'.format(url, req.status_code))
            exit(1)

        yield bs4.BeautifulSoup(req.content, 'html.parser')

    def deploy(self, word):
        with self.soup(word) as soup:
            match = soup.find(class_='keyword')
            if match:
                # pronunciation
                wordbook = soup.find(class_='wordbook-js')
                _pronounce = wordbook.find_all(class_='pronounce')
                pronounces = []
                translate = []
                web_translate = []
                word_phrase = []
                if not _pronounce:
                    _pronounce = wordbook.find_all(class_='phonetic')
                for p in _pronounce:
                    temp = p.get_text().replace(' ', '').replace('\n', '')
                    if not temp:
                        continue
                    pronounces.append(p.get_text().replace(' ', '').replace('\n', ''))

                # translation
                _trans = soup.find(class_='trans-container')
                if _trans and _trans.find('ul'):
                    _normal_trans = _trans.find('ul').find_all('li')
                    if not _normal_trans:
                        _normal_trans = _trans.find('ul').find_all(class_='wordGroup')
                    for _nt in _normal_trans:
                        title = _nt.find(class_='contentTitle')
                        type_ = _nt.find('span')
                        if title and type_:
                            title = title.get_text()
                            type_ = type_.get_text()
                        else:
                            title = _nt.get_text()
                            type_ = ''
                        tmp = (type_ + title).replace('\n', '')
                        if tmp.count(' ') > 4:
                            tmp = tmp.replace("  ", '')
                        translate.append(tmp)

                # web translation
                _web_trans = soup.find(id="tWebTrans")
                if _web_trans:
                    for i in _web_trans.find_all('span', class_=None):
                        temp = i.get_text().replace('\n', '').replace(' ', '')
                        if not temp:
                            continue
                        web_translate.append(temp)

                    # word phrase
                    _word_phrase = _web_trans.find(id='webPhrase')
                    if _word_phrase:
                        for i in _word_phrase.find_all(class_='wordGroup'):
                            title = i.find(class_='contentTitle')
                            if not title:
                                continue
                            title = title.get_text()
                            word_phrase.append({
                                'phrase': title,
                                'explain': i.get_text().replace('\n', '').replace(title, '').replace(' ', '')
                            })

                # print word_phrase
                # print translate
                # print web_translate
                # print pronounces
                return 0, {
                    'pronounces': pronounces,
                    'translate': translate,
                    'web_translate': web_translate
                }
            else:
                similar = soup.find(class_='error-typo')
                if similar:
                    possibles = []
                    similar = similar.find_all(class_='typo-rel')
                    for s in similar:
                        title = s.find(class_='title')
                        content = s.get_text()
                        if title:
                            title = title.get_text().replace(' ', '').replace('\n', '')
                            content = content.replace(title, '').replace(' ', '').replace('\n', '')
                        else:
                            continue
                        possibles.append({
                            'possible': title,
                            'explain': content
                        })
                    return 1, {
                        'possibles': possibles
                    }
                return None, None

if __name__ == '__main__':
    dic = readfile('dic.txt')
    for word in dic:
        print word
        _, result = Spider().deploy(word)
        if len(result['pronounces']) >= 1:
            print result['pronounces'][0]
        for str in result['translate']:
            print str