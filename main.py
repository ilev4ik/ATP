import requests
from time import sleep
import xml.etree.ElementTree as ET
from html2text import html2text
from bs4 import BeautifulSoup
import pymorphy2
import re
from math import log10, sqrt
from itertools import combinations
from tabulate import tabulate
import codecs

morpher = pymorphy2.MorphAnalyzer()

key = '03.376324790:e8890cb21bb8db64b9afa1cac5f89642'
doc_num = 10


def write_to_file(text):
    with codecs.open('result.txt', 'a', 'utf-8') as file:
            file.write(text+'\n')


def get_words_of(text):
    word_list = re.split('\W+', text.lower())
    word_list = list(filter(lambda token: '_' not in token and token, word_list))
    return word_list


def doc_cos(q, d):
    d_scores = [d[key] for key in sorted(d)]
    q_scores = [q[key] for key in sorted(q)]
    numerator = sum([a * b for (a, b) in zip(q_scores, d_scores)])
    denomenator = sqrt(sum([a ** 2 for a in q_scores])) * sqrt(sum([b ** 2 for b in d_scores]))
    if denomenator == 0:
        return 0
    return numerator / denomenator

query_key_list = ['хоккей', 'футбол', 'автомобили', 'программирование', 'математика']
for key_word in query_key_list:
    global key
    query = key_word + ' site:www.livejournal.com/media lang:ru'
    write_to_file('Query: ' + query)


    options = {
        'user': 'ilev4ik-hse',
        'key': key,
        'query': query,
        'l10n': 'en',
        'sortby': 'tm.order%3Dascending',
        'filter': 'strict',
        'groupby': 'attr%3D%22%22.mode%3Dflat.groups-on-page%3D15.docs-in-group%3D1',
        'page': '1'
    }

    results = ET.ElementTree
    while True:
        r = requests.get('https://yandex.com/search/xml', options)

        root = ET.fromstring(r.text)
        # при неудачном ответе response не будет определён
        try:
            response = root[1]
            results = response[-1]
            print("good response")
        except IndexError:
            sleep(1)
            continue
        break

    # with codecs.open(key+'.xml', 'w', 'utf-8') as f:
    #     xml = xml.dom.minidom.parseString(r.text)
    #     f.write(xml.toprettyxml())

    current_doc_num = 0
    text_list = list()
    url_list = list()
    for (idx, url) in enumerate(results.iter('url')):
        url = url.text
        print(url, "started", end=" ")
        try:
            html = requests.get(url).text
        except Exception:
            print("oops")
            continue
        parsed_html = BeautifulSoup(html, 'lxml')
        article = parsed_html.body.find('div', attrs={'class': 'mdspost-text'})
        try:
            text = html2text(article.text)
        except AttributeError:
            print(idx, "skipped")
            sleep(1)
            continue
        text_list.append(text)
        url_list.append(url)
        print(idx, 'done')
        current_doc_num += 1
        write_to_file(url)
        if current_doc_num == 10:
            break
        sleep(1)

    print("texts parsed")




    terms_list = []             # список всех слов во всех текстах
    text_terms_list = []        # список словарей слов для каждого текста

    for (id, text) in enumerate(text_list):
        word_list = get_words_of(text)
        text_terms_list.append(dict())
        for word in word_list:
            p = morpher.parse(word)[0]
            normal_word = p.normal_form

            if ('NPRO' not in p.tag or
                 'PRED' not in p.tag or
                 'CONJ' not in p.tag or
                 'PRCL' not in p.tag or
                 'INTJ' not in p.tag or
                 'PREP' not in p.tag
                ):

                if normal_word in text_terms_list[id]:
                    text_terms_list[id][normal_word] += 1
                else:
                    text_terms_list[id].update({normal_word: 1})

                if normal_word not in terms_list:
                    terms_list.append(normal_word)


    tf_table = []
    for terms in text_terms_list:
        d = dict().fromkeys(terms_list, 0)
        d.update(terms)
        tf_table.append(d)

    N = len(terms_list) # кол-во различных терминов в коллекции
    doc_freq = dict().fromkeys(terms_list, 0)
    for key in terms_list:
        for doc in tf_table:
            doc_freq[key] += doc[key] > 0

    # вес термина t в документе d = tf*idf
    for tf_dict in tf_table:
        for (term, tf) in tf_dict.items():
            tf_dict[term] = tf*log10(N/doc_freq[term])

    L = range(0,current_doc_num,1)
    uniqe_pair_list = [comb for comb in combinations(L, 2)]

    range_dict = {}
    n = current_doc_num
    matrix = [['-' for x in range(n+1)] for y in range(n)]
    for (i,j) in uniqe_pair_list:
        matrix[i][j+1] = round(doc_cos(tf_table[i], tf_table[j]), 3)

    url_list = [url.split('/')[-1].split('.')[0] for url in url_list]
    for j in range(n):
        matrix[j][0] = url_list[j]

    write_to_file(tabulate(matrix, headers=url_list, tablefmt='orgtbl'))
