# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import base64
import time
from scrapy import signals
import random
import re
from urllib import parse
import requests
from .settings import PROXY_USER, PROXY_PASS
from .agent import agents
from scrapy_crawlera import CrawleraMiddleware


class DataitemSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        # crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        # return s
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

    def process_request(self, request, spider):
        if request.meta.get('request_tp') == 'store':
            # request.meta['proxy'] = self.luminati

            request.meta['proxy'] = self.proxyServer
            request.headers['Proxy-Authorization'] = self.proxyAuth

        if request.meta.get('request_tp') == 'detail':
            super().process_request(request, spider)


class MixProxyDownloaderMiddleware(CrawleraMiddleware):
    # 阿布云代理
    abuyun_proxy = "http://http-dyn.abuyun.com:9020"
    abuyun_auth = "Basic " + base64.urlsafe_b64encode(bytes((PROXY_USER + ":" + PROXY_PASS), "ascii")).decode("utf8")

    # 蘑菇代理
    mogu_proxy = "http://transfer.mogumiao.com:9001"
    mogu_appkey = "Basic " + 'MWdxTHVRcVNNOWFMd3RPUzoyV0pFRnhhM1NKQlc4djhC'

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


class CMiddleware(CrawleraMiddleware):
    def process_request(self, request, spider):
        if request.meta.get('no_crawlera'):
            return
        super().process_request(request, spider)
