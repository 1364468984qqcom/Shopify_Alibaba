# -*- coding: utf-8 -*-

"""
使用接口及登录cookie获取店铺列表

"""

import logging
import copy
import random
import re
import time
import hashlib
import json
import requests
import scrapy

from html import unescape
from DataItem.redis_pool import RedisPool
from DataItem.agent import item_list_hd, site_dict


class TbshopspiderSpider(scrapy.Spider):
    name = 'TbShopSpider1'
    allowed_domains = ['taobao.com', 'tmall.com']
    redis_key = "all_spider:strat_urls"
    logger = logging.getLogger('ShopSpider')
    cookie_used = 0

    custom_settings = {
        # 'CRAWLERA_ENABLED': False
        'CONCURRENT_REQUESTS': 50,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 50,
        # 'DOWNLOAD_DELAY': 5
    }

    def __init__(self, **kwargs):
        # 初始化redis
        self.rdb = RedisPool()
        self.reds_conn = self.rdb.redis_con()

        # 初始化请求类别, 用于区别代理
        self.request_tp = ('store', 'detail')

        # 初始化url
        self.baseurl = 'http://shop.m.taobao.com/shop/shopsearch/search_page_json.do?sort=default&type=all&q='
        self.store_detail = ('http://h5api.m.taobao.com/h5/mtop.taobao.geb.shopinfo.queryshopinfo/2.0/?jsv=2.4.2'
                             '&appKey={appkey}&t={t}&sign={sign}&api=mtop.taobao.geb.shopinfo.queryshopinfo&v=2.0'
                             '&type=originaljson&timeout=3000&AntiCreep=true&dataType=json&H5Request=true&data={data}')
        self.login_shopping_list = ('https://h5api.m.taobao.com/h5/com.taobao.search.api.getshopitemlist/2.0/?jsv=2.4.2'
                                    '&appKey={appkey}&t={t}&sign={sign}&api=com.taobao.search.api.getShopItemList&v=2.0'
                                    '&type=jsonp&dataType=jsonp&callback=mtopjsonp7&data={data}')
        self.logout_shopping_list = 'https://h5api.m.taobao.com/h5/mtop.taobao.wireless.shop.index.wandering.get/1.0/?appKey={appkey}&t={t}&sign={sign}&data={data}'

        # 初始化详情正则对象
        self.all_pids = []
        self.job_id = kwargs.get('_job', 123)
        self.callback = kwargs.get('callback', 'http://products.kuyun.loc/api/screen/shop')
        self.s_id = kwargs.get('s_id')
        self.title = ''
        self.seller_name = ''
        self.retry = 0  # 搜索店铺尝试次数
        self.logger.info(f'Received: {kwargs}')
        self.shop_id = 0

        # cookie必要参数初始化
        self.appkeys = '12574478'
        self.login_token = self.get_login_token()
        self.logout_token = self.get_logout_token()
        ctk = self.logout_token
        self.h5_token = ctk.get('token')
        self.cookie = ctk.get('strcookie')
        self.dict_cookies = ctk.get('dict_cookies')
        self.taobao_header = item_list_hd
        self.taobao_header.update({'cookie': self.cookie})
        super().__init__(**kwargs)

    # 根据cookie获取token
    def get_login_token(self):
        cookie_info = self.rdb.hgetall('login_cookie')
        cookie_list = []
        for cookie in cookie_info:
            # login_cookie = cookie_info[list(cookie_info)[int(self.s_id) % len(cookie_info)]]  # 循环取cookie
            token = ''.join(re.findall('_m_h5_tk=([^;]+);', cookie_info[cookie])).split('_')[0]
            dict_cookies = dict([tuple(x.split('=', 1)) for x in cookie_info[cookie].split(';')])
            cookie_list.append({'token': token, 'strcookie': cookie_info[cookie], 'dict_cookies': dict_cookies})
        return cookie_list

    def get_logout_token(self):
        cookie = self.rdb.rget('logout_cookie')
        token = ''.join(re.findall('_m_h5_tk=([^;]+);', cookie)).split('_')[0]
        dict_cookies = dict([tuple(x.split('=', 1)) for x in cookie.split(';')])
        return {'token': token, 'strcookie': cookie, 'dict_cookies': dict_cookies}

    # 根据所需元素计算sign
    def sign(self, token, appkey, t, data):
        pp = '&'.join([token, t, appkey, data]).encode()
        sign = hashlib.md5(pp).hexdigest()
        return {'sign': sign, 't': t, 'appkey': appkey, 'data': data}

    # redis里以scrapyd分发的jobid为key取后端发来的数据
    def start_requests(self):
        # n = 0
        # while True:
        #     n += 1
        #     resp = self.reds_conn.hget('_all_shop', self.s_id)
        #     if resp or n > 500:
        #         break
        #     time.sleep(1)
        #
        # if resp:
        #     data = json.loads(resp)
        # else:
        #     self.logger.warning(f'Shop Id Error: {self.s_id}')
        #     return

        data = {
            'id': '10086',
            'title': '优衣库官方旗舰店',
            'shop_id': '57303596',
            'name': '优衣库官方旗舰店',
            'shop_link': 'https://uniqlo.tmall.com'
        }
        sid, title, seller_name, shop_id = (self.s_id, data.get('title'), data.get('name'), data.get('shop_id'))
        self.title, self.seller_name, self.shop_id = title, seller_name, shop_id
        yield scrapy.Request(url=self.baseurl + title, headers=self.taobao_header,
                             cookies=self.dict_cookies, callback=self.parse_search,
                             meta={'sid': sid, 'shopid': shop_id})

    # 搜索店铺信息并匹配
    def parse_search(self, response):
        re_dt = {}
        shopid = response.meta.get('shopid')
        sid = response.meta.get('sid', 0)
        doc = unescape(response.text)
        jd_data = json.loads(doc)
        if jd_data.get('listItem'):
            for s in jd_data.get('listItem'):
                try:
                    if str(shopid) in str(s):
                        re_dt['sign'] = str(sid)  # sign 产品库id
                        re_dt['shopid'] = str(s.get('shop').get('id'))  # 淘宝shopid
                        re_dt['is_mall'] = s.get('shop').get('isMall')  # 是否天猫
                        re_dt['total_sold'] = str(s.get('shop').get('totalSold'))  # 销量
                        re_dt['level'] = ''.join(re.findall('\d-\d', str(s.get('icon'))))  # 店铺等级
                        re_dt['sellerid'] = ''.join(re.findall('userid=(\d+)', str(s.get('medal'))))  # 卖家id
                        re_dt['goods'] = s.get('favRate')  # 好评率
                        break
                    else:
                        self.logger.error('search title is failure!')
                except:
                    continue
        else:
            self.logger.error('search title is failure!')

        # 如果用掌柜ID查找不到的话就用店铺名称查找

        if not re_dt and self.retry == 0:
            self.retry += 1
            yield scrapy.Request(url=self.baseurl + self.seller_name, headers=self.taobao_header,
                                 cookies=self.dict_cookies, callback=self.parse_search,
                                 meta={'sid': sid, 'shopid': shopid})
            return
        if not re_dt and self.retry == 1:
            self.logger.error('final search title is failure!')
            return
        cookie = self.logout_token
        hd = self.taobao_header
        hd.update({'cookie': cookie.get('strcookie'), 'X-Crawlera-Cookies': 'disable'})
        data = '{"sellerId": %s}' % re_dt.get('sellerid')
        st = self.sign(token=cookie.get('token'), appkey=self.appkeys, t=str(int(time.time() * 1000)), data=data)
        yield scrapy.Request(url=self.store_detail.format(**st), headers=hd,
                             cookies=cookie.get('dict_cookies'), callback=self.parse_store_item,
                             meta={'re_data': json.dumps(re_dt)})
        self.cookie_used += 1

    # 进一步抓取店铺信息
    def parse_store_item(self, response):
        re_data = json.loads(response.meta.get('re_data'))
        doc = json.loads(response.text)
        tdt = doc.get('data')
        if not tdt:
            self.logger.error(f'Crawl Failed! DOC:{doc}')
            return
        count = tdt.get('itemCount')
        re_data['shopname'] = tdt.get('shopName')  # 店铺名
        re_data['fans_num'] = str(tdt.get('fansNum'))  # 粉丝数
        re_data['item_count'] = str(count)  # 产品数量
        re_data['new_item'] = str(tdt.get('newItem'))  # 新品数
        re_data['golden_seller'] = tdt.get('goldenSeller')  # 金牌卖家
        seller_id = tdt.get('sellerId')
        self.logger.info(f'post data: {json.dumps(re_data)}')
        self.reds_conn.hset('_shop_info', re_data['shopname'], json.dumps(re_data))
        # 根据后端相应回调站点取相应的验证信息,然后将信息发送到回调
        headers = site_dict[self.callback]['headers']
        r = requests.post(self.callback, data=json.dumps(re_data), headers=headers, timeout=50)
        if r.status_code == 200:
            if r.json().get('status') == 200:
                self.logger.info(f'post success')
            else:
                self.logger.info(f'shop post return: {r.text}')
        pdata = '{"shopId":"%s","currentPage":1,"pageSize":"100","sort":"oldstarts","q":""}' % str(re_data['shopid'])
        self.logger.info(f'prod count:{count}')
        # self.get_list_from_login(count, pdata)
        self.get_list_from_logout(count, seller_id)
        # yield scrapy.Request(url=self.shopping_list.format(**sign), headers=hd, cookies=cookie.get('dict_cookies'),
        #                      callback=self.shop_list_item, dont_filter=True,
        #                      meta={'pdata': data,
        #                            # 'request_tp': self.request_tp[0]
        #                            })
        # pns = int(int(count) / 10) + 2
        # for pn in range(1, pns):
        #     cookie = self.logout_token
        #     hd = self.taobao_header
        #     hd.update({'cookie': cookie.get('strcookie')})
        #     data = json.dumps({"direction": 1, "userId": seller_id, "pageSize": 10, "needPreNew": True, "curPage": pn})
        #     sign = self.sign(cookie.get('token'), self.appkeys, str(int(time.time() * 1000)), data)
        #     url = self.logout_shopping_list.format(**sign)
        #     cookies = cookie.get('dict_cookies')
        #     yield scrapy.Request(url=url, headers=hd, cookies=cookies, callback=self.shop_list_item_logout, dont_filter=True,
        #                          meta={'request_tp': self.request_tp[1]},
        #                          )


    # 需要登陆cookie
    def get_list_from_login(self, count, pdata):
        pns = int(int(count) / 100) + 2
        for pn in range(1, pns):
            cookie = self.login_token[pn % len(self.login_token)]
            hd = self.taobao_header
            hd.update({'cookie': cookie.get('strcookie')})
            data = re.sub('currentPage":\d+', 'currentPage":' + str(pn), pdata)
            sign = self.sign(cookie.get('token'), self.appkeys, str(int(time.time() * 1000)), data)
            r = requests.get(self.login_shopping_list.format(**sign), headers=hd)
            time.sleep(random.uniform(3, 3.6))
            doc = re.sub('mtopjsonp\d+\(', '', r.text)[:-1]
            doc = json.loads(doc)
            re_dl = []
            if doc.get('data') and doc.get('data').get('itemsArray'):
                re_dl.extend(doc.get('data').get('itemsArray'))

            if not re_dl:
                self.logger.error(f'{doc}')
                continue
            pids = [x.get('auctionId') for x in re_dl]
            self.all_pids.extend(pids)  # 每一页商品id存入总列表

    # 需要非登陆cookie
    def get_list_from_logout(self, count, seller_id):
        pns = int(int(count) / 10) + 2
        for pn in range(1, pns):
            cookie = self.logout_token
            hd = self.taobao_header
            hd.update({'cookie': cookie.get('strcookie')})
            data = json.dumps({"direction": 1, "userId": seller_id, "pageSize": 10, "needPreNew": True, "curPage": pn})
            sign = self.sign(cookie.get('token'), self.appkeys, str(int(time.time() * 1000)), data)
            yield scrapy.Request(url=self.logout_shopping_list.format(**sign), headers=hd,
                                 meta={'request_tp': self.request_tp[1]},
                                 cookies=cookie.get('dict_cookies'), callback=self.shop_list_item_logout)

    def shop_list_item_logout(self, response):
        data = response.text
        res = data.get('data', dict()).get('result')
        if res:
            ids = [i['blockContent']['itemId'] for i in res]
            self.all_pids.extend(ids)

    # 按页抓取店铺里的商品列表
    def shop_list_item(self, response):
        doc = re.sub('mtopjsonp\d+\(', '', response.text)[:-1]
        doc = json.loads(doc)
        re_dl = []
        if doc.get('data') and doc.get('data').get('itemsArray'):
            re_dl.extend(doc.get('data').get('itemsArray'))

        if not re_dl:
            self.logger.error('store list re_dl is null..')
            return

        pids = [x.get('auctionId') for x in re_dl]
        self.all_pids.extend(pids)  # 每一页商品id存入总列表

    # 店铺爬虫结束后,数据存入redis并调用商品详情爬虫
    def close(self, spider, reason):
        self.reds_conn.hset('_detail', self.job_id, json.dumps(self.all_pids))
        post_data = dict()
        post_data['project'] = 'DataItem'
        post_data['spider'] = 'TbDetailSpider'
        post_data['Shop_jobid'] = self.job_id
        post_data['callback'] = self.callback
        post_data['s_id'] = self.s_id
        post_data['title'] = self.title
        post_data['seller_name'] = self.seller_name
        post_data['shop_id'] = self.shop_id
        r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
        self.logger.info(f'length of all pids: {len(self.all_pids)}')
