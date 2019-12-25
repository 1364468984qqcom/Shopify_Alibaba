# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import base64
import time

import redis
from scrapy import signals
import random
import re
from urllib import parse
import requests
from .settings import PROXY_USER, PROXY_PASS
from .agent import agents
# from data_utils.cookie_pool import CreateCookie
from scrapy_crawlera import CrawleraMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class DataitemSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DataitemDownloaderMiddleware(object):
    N = 0
    dt_cookie = None

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        if request.meta.get('request_tp') == 'store' and 'currentPage' in request.url:
            if self.N == 0:
                self.dt_cookie = spider.rdb.get_cookie()
            self.N = self.N + 1
            if self.N % 10 == 0:
                self.dt_cookie = spider.rdb.get_cookie()
            tags = re.findall('&data=({.+?})', parse.unquote(request.url))
            token = ''.join(re.findall('_m_h5_tk---([^;]+);', self.dt_cookie)).split('_')[0]
            dict_cookies = dict([tuple(x.split('---')) for x in self.dt_cookie.split(';')])
            ss = spider.sign(token, spider.appkeys, str(int(time.time() * 1000)), tags[0])
            request._set_url(spider.shopping_list.format(**ss))
            request.headers['cookie'] = self.dt_cookie.replace('---', '=')
            request.headers['user-agent'] = random.choice(agents)
            request.cookies = dict_cookies

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxyDownloaderMiddleware(CrawleraMiddleware):
    # 代理服务器
    proxyServer = "http://http-dyn.abuyun.com:9020"

    # 生成加密后的代理密码
    proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((PROXY_USER + ":" + PROXY_PASS), "ascii")).decode("utf8")

    luminati = 'http://lum-customer-hl_e4a2a192-zone-static:5kdz519e6rrc@zproxy.lum-superproxy.io:22225'

    # def __init__(self, *args, **kwargs):
    #     pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=0)
    #     self.reds = redis.Redis(connection_pool=pool)
    #     self.cookie_used = 0
    #     cookie = self.set_token()
    #     self.cookie = self.get_token(cookie)
    #     super().__init__(*args, **kwargs)

    def set_token(self):
        print(10086)
        browser = CreateCookie()
        cookie = browser.set_time_cookie()
        return cookie

    def process_request(self, request, spider):
        if request.meta.get('request_tp') == 'store':
            # request.meta['proxy'] = self.luminati

            request.meta['proxy'] = self.proxyServer
            request.headers['Proxy-Authorization'] = self.proxyAuth
            # request.cookies = self.cookie.get('dict_cookies')
            # if self.cookie_used > 20:
            #     self.get_token()

        if request.meta.get('request_tp') == 'detail':
            super().process_request(request, spider)

    def get_token(self, cookie):
        token = ''.join(re.findall('_m_h5_tk---([^;]+);', cookie)).split('_')[0]
        dict_cookies = dict([tuple(x.split('---')) for x in cookie.split(';')])
        return {'token': token, 'strcookie': cookie.replace('---', '='), 'dict_cookies': dict_cookies}


class CMiddleware(CrawleraMiddleware):
    def process_request(self, request, spider):
        if request.meta.get('no_crawlera'):
            return
        super().process_request(request, spider)


class MixProxyDownloaderMiddleware(CrawleraMiddleware):
    # 阿布云代理
    abuyun_proxy = "http://http-dyn.abuyun.com:9020"
    abuyun_auth = "Basic " + base64.urlsafe_b64encode(bytes((PROXY_USER + ":" + PROXY_PASS), "ascii")).decode("utf8")

    # 蘑菇代理
    ip_port = 'transfer.mogumiao.com:9001'
    appKey = 'MWdxTHVRcVNNOWFMd3RPUzoyV0pFRnhhM1NKQlc4djhC'
    proxy = {"http": "http://" + ip_port, "https": "https://" + ip_port}
    # 讯代理
    xun_api = 'http://api.xdaili.cn/xdaili-api//newExclusive/getIp?spiderId=8eb80014a27044a2a1717f40289a7543&orderno=DX20192116447Oaz02G&returnType=1&count=1&machineArea='

    # 芝麻代理
    zhima_api = 'http://http.tiqu.alicdns.com/getip3?num=1&type=1&pro=&city=0&yys=0&port=11&pack=40305&ts=0&ys=0&cs=0&lb=4&sb=0&pb=4&mr=2&regions='

    # 缓存一个最新的代理ip
    xz_ip = None

    def help_request(self, px):
        try:
            doc = requests.get(px, timeout=3)
            tags = re.findall('[\d\.\:]{10,}', doc.text.replace(' ', ''))
            ips = ['http://' + x for x in tags]
        except:
            return self.xz_ip

        if ips:
            return {'proxy': random.choice(ips)}
        else:
            print('proxy_ips_list request is error!')
            return self.xz_ip

    def process_request(self, request, spider):
        if spider.name == 'TbShopSpider' and not request.meta.get('proxy'):
            request.meta['proxy'] = self.abuyun_proxy
            request.headers['Proxy-Authorization'] = self.abuyun_auth

        if request.meta.get('_error_flag'):
            # 赋值特殊代理ip
            if request.meta['_error_flag'] == 1:
                request.meta['proxy'] = self.mogu_proxy
                request.headers['Authorization'] = self.mogu_appkey
            elif request.meta['_error_flag'] == 2:
                resp = self.help_request(self.xun_api)
                self.xz_ip = resp.get('proxy')
                request.meta['proxy'] = self.xz_ip
            elif request.meta['_error_flag'] == 3:
                resp = self.help_request(self.zhima_api)
                self.xz_ip = resp.get('proxy')
                request.meta['proxy'] = self.xz_ip

        # scrapy自己的代理
        if spider.name == 'TbDetailSpider':
            if request.meta.get('no_crawlera'):
                return
            super().process_request(request, spider)

    def process_response(self, request, response, spider):
        if response.status > 300 or 'anti_Spider' in str(response.url) or "{'data': []}" in response.text:
            # 失败次数标记
            if request.meta.get('_error_flag'):
                request.meta['_error_flag'] = request.meta.get('_error_flag') + 1
            else:
                request.meta['_error_flag'] = 1

            if request.meta.get('_error_flag') == 4:
                spider.rdb.failure_save(request.url)
                return response

            return request

        else:
            return response


class CookiePoolDownloaderMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        pass


class CreateCookie(object):
    def __init__(self):
        self.T = 3000  # 过期时间
        self.save_key = 'queue_cookie'
        self.website = 'https://h5.m.taobao.com/'
        self.redis_conn = redis.Redis(host='127.0.0.1', port=6379, db=0)
        # self.driver = self.init_drive()

    def init_drive(self):
        for i in range(0, 3):
            try:
                # 设置成手机模式
                mobile_emulation = {"deviceName": "iPhone X"}
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument("window-size=2436, 1125")
                options.add_argument("--no-sandbox")
                options.add_experimental_option("mobileEmulation", mobile_emulation)
                options.add_argument(
                    'user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"')

                driver = webdriver.Chrome(executable_path=r'D:\GitHub\TbShop\DataItem\data_utils\chromedriver.exe',
                                          options=options)
                return driver
            except Exception as e:
                print(e)
                continue
        return

    def get_cookie_by_PhantomJS(self, domain):
        for i in range(0, 3):
            driver = self.init_drive()
            try:
                driver.get(domain)
                time.sleep(0.5)
                cookies = driver.get_cookies()
                cookie = [item["name"] + "---" + item["value"] for item in cookies]

                cookiestr = ';'.join(item for item in cookie)
                return cookiestr
            except Exception as e:
                print(e)
                continue
            finally:
                driver.quit()
        return

    def create_cookies(self):
        while True:
            cookie = self.get_cookie_by_PhantomJS(self.website)
            if cookie:
                self.redis_conn.lpush(self.save_key, cookie)
            else:
                print('cookie create is error!')
            time.sleep(15)

    def set_time_cookie(self):
        print(10086)
        cookie = self.get_cookie_by_PhantomJS(self.website)
        if cookie:
            self.redis_conn.lpush(self.save_key, cookie)
            self.redis_conn.ltrim(self.save_key, 0, 200)
        else:
            print('cookie create is error!')
        return cookie
