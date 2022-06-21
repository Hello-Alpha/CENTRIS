import json
import re
import os
import sys
import requests
import threading
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pymysql
from lxml import etree

fullname = "tmp.txt"
standard_output = sys.stdout
git = []
tags = []
count = 0
access_flag = False

def Change_UA():
    ua = UserAgent()
    browser = ['ie', 'chrome', 'firefox', 'safari']
    return ua[(browser[random.randint(0, 3)])]


def get_proxy():
    global proxys
    proxys = []
    content = requests.get("https://www.kuaidaili.com/free/inha/1/")
    content.encoding = content.apparent_encoding
    text = content.text
    soup = BeautifulSoup(text, 'html.parser')
    soup = soup.tbody
    IPS = soup.find_all(attrs={'data-title': 'IP'})
    PORTS = soup.find_all(attrs={'data-title': 'PORT'})
    for i in range(0, len(IPS)):
        proxy = '%s:%s' % (IPS[i].string, PORTS[i].string)
        proxys.append(proxy)


def random_proxy():
    proxy = proxys[random.randint(0, len(proxys) - 1)]
    return proxy


def get(url):
    global access_flag
    access_flag = False
    proxies = {'http': 'http://%s' % (random_proxy())}
    global no_get
    UA = Change_UA()
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip,deflate,br',
        'Connection': 'Upgrade',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': UA,
        'referer': 'https://github.com',
        'Authorization': 'token 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',
    }
    try:
        content = requests.get(url=url, headers=headers, proxies=proxies, timeout=5)
        time.sleep(0.5)
        return content
    except requests.exceptions.RequestException as e:
        print('无法访问：%s' % url)
        access_flag = True
        return None


def each_page(url):
    global git
    global count
    global access_flag
    print("git总计:", len(git))
    wb_data = get(url)
    while access_flag:
        print(url, "无法访问！,摆烂！30s")
        time.sleep(30)
        wb_data = get(url)
    if wb_data.status_code == 404:
        return 1
    while wb_data.status_code == 429:
        print(url, "无法访问！,摆烂！30s")
        time.sleep(30)
        wb_data = get(url)
    flag = 0
    text = wb_data.content.decode('UTF-8')
    json_dict = json.loads(text)
    total_count = json_dict['total_count']
    for item in json_dict['items']:
        count += 1
        if count > total_count:
            flag = 1
            break
        target = item['html_url'] + "/archive/refs/heads/master.zip"
        star = item['stargazers_count']
        language = item['language']
        if star > 1000:
            if language == "Python" and target not in git:
                git.append(target)
                with open(fullname, "a+", encoding='utf-8') as f:
                    sys.stdout = f
                    print(target)
                    sys.stdout = standard_output
                    print(target)
        else:
            flag = 1
            break
    return flag


def tag_collect(url):
    print("tag's fetching url is ", url)
    global tags
    wb_data = get(url)
    while access_flag:
        print(url, "无法访问！,摆烂！30s")
        time.sleep(30)
        wb_data = get(url)
    if wb_data.status_code == 404:
        return 1
    while wb_data.status_code == 429:
        print(url, "无法访问！,摆烂！30s")
        time.sleep(30)
        wb_data = get(url)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    for node in soup.find_all("a", attrs={'data-ga-click': 'Topic, search results'}):
        nstr = ""
        tmp = node.string
        nstr = nstr.join(tmp)
        nstr = nstr.strip()
        if nstr not in tags:
            tags.append(nstr)
    time.sleep(1)

def main():
    global count
    get_proxy()  #proxys存储可用的proxy
    tag_collect("https://github.com/search?l=Python&o=desc&p=1&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=2&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=3&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=4&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=5&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=6&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=7&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=8&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=9&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=10&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=11&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=12&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=13&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=14&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=15&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=16&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=17&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=18&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=19&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=20&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=21&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=22&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=23&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=24&q=python&s=stars&type=Repositories")
    tag_collect("https://github.com/search?l=Python&o=desc&p=25&q=python&s=stars&type=Repositories")

    print(tags)
    print("[GCX DEBUG] python")
    count = 0
    for i in range(10):
        print("[GCX DEBUG] 页码:", i + 1)
        url = "https://api.github.com/search/repositories?q=python+language:python&sort=stars&order=desc&per_page=100&page=" + str(i + 1)
        print("fetching url is ", url)
        if each_page(url):
            break
        # time.sleep(1)
    for tag in tags:
        count = 0
        if tag == "python":
            continue
        print("[GCX DEBUG] ", tag)
        for i in range(10):
            print("[GCX DEBUG] 页码:", i+1)
            url = "https://api.github.com/search/repositories?q="+tag+"+language:python&sort=stars&order=desc&per_page=100&page="+str(i+1)
            print("fetching url is ", url)
            if len(git) > 8000:
                break
            if each_page(url):
                break
            # time.sleep(1)


if __name__ == '__main__':
    main()
