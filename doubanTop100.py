# -*- coding:utf-8 -*-
"""
__mktime__ = '2017/7/20'
__author__ = 'bonree'
__filename__ = 'doubanTop100'
"""
import json
from multiprocessing import Pool
import requests
import re
from requests.exceptions import RequestException


def get_one_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response
        return None
    except RequestException:
        return None


def parse_one_page(html):
    pattern = re.compile('.*?<dd>.*?board-index.*?(\d+)</i>.*?data-src="(.*?)".*?"name"><a.*?">(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>.*?"integer">(.*?)</i>.*?(\d+)</i></p>.*?</dd>', re.S)
    results = re.findall(pattern, html)
    for result in results:
         yield {
            "index": result[0],
            "image": result[1],
            "title": result[2],
            "star":  result[3].strip(),
            "date":  result[4].strip()[5:],
            "score": result[5] + result[6]
        }


def write_to_file(content):
    with open('douban.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


def main(offset):
    html = get_one_page('http://maoyan.com/board/4?offset=' + str(offset))
    for item in parse_one_page(html.text):
        print(item)
        write_to_file(item)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [i*10 for i in range(10)])
