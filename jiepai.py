# -*- coding:utf-8 -*-
"""
__mktime__ = '2017/7/20'
__author__ = 'bonree'
__filename__ = 'jiepai'
"""
import json
import os
from multiprocessing.pool import Pool
from urllib.parse import urlencode
from hashlib import md5
import re

import pymongo
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from toutiao.config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]


def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1
    }
    params = urlencode(data)
    base = 'http://www.toutiao.com/search_content/'
    url = base + '?' + params
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('获取索引页面失败', url)
        return None


def parse_page_index(text):
    data = json.loads(text)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')


def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    result = soup.select('title')
    title = result[0].get_text() if result else ''
    image_pattern = re.compile('gallery = (.*?);', re.S)
    results = re.search(image_pattern, html)
    if results:
        data = json.loads(results.group(1))
        if data and 'sub_images' in data.keys():
            sub_images = data['sub_images']
            images = [item['url'] for item in sub_images]
            for image in images:
                download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }


def get_page_detial(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print(url)
        print('获取详情页面失败 {0}'.format(url))
        return None


def save_image(content):
    image_path = os.path.join(os.path.dirname(__file__), 'images')
    file_path = '{0}/{1}.{2}'.format(image_path, md5(content).hexdigest(), 'jpg')
    with open(file_path, 'wb') as f:
        f.write(content)
        f.close()


def download_image(url):
    print('downloading ' + url)
    response = requests.get(url)
    if response.status_code == 200:
        save_image(response.content)
    return None


def save_to_mongo(image):
    if db[MONGO_TABLE].insert(image):
        print('Successfully Saved to Mongo', image)
        return True
    return False


def main(offset):
    text = get_page_index(offset, KEYWORD)
    urls = parse_page_index(text)
    for url in urls:
        html = get_page_detial(url)
        if html:
            result = parse_page_detail(html, url)
            if result:
                save_to_mongo(result)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [item*20 for item in range(GROUP_START, GROUP_END + 1)])
    pool.close()
    pool.join()

