# -*- coding: utf-8 -*-
import logging
import copy
import re
import time
import hashlib
import json
import requests
import scrapy

from DataItem.redis_pool import RedisPool
from DataItem.agent import item_list_hd, site_dict

"""
使用原始接口及登录cookie获取店铺列表(origin version)

"""


class TbshopspiderSpider(scrapy.Spider):
    name = 'TbShopSpider_o'
    allowed_domains = ['taobao.com', 'tmall.com']
    redis_key = "all_spider:strat_urls"
    logger = logging.getLogger('ShopSpider')
    cookie_used = 0

    custom_settings = {
        # 'CRAWLERA_ENABLED': False
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1
    }

    def __init__(self, **kwargs):
        self.n = 0
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
        self.shopping_list = ('https://h5api.m.taobao.com/h5/com.taobao.search.api.getshopitemlist/2.0/?jsv=2.4.2'
                              '&appKey={appkey}&t={t}&sign={sign}&api=com.taobao.search.api.getShopItemList&v=2.0'
                              '&type=jsonp&dataType=jsonp&callback=mtopjsonp7&data={data}')

        # cookie必要参数初始化
        self.appkeys = '12574478'
        ctk = self.get_token()
        self.h5_token = ctk.get('token')
        self.cookie = ctk.get('strcookie')
        self.dict_cookies = ctk.get('dict_cookies')
        self.taobao_header = {
            'user-agent': 'user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"'}

        # 初始化详情正则对象
        self.all_pids = []
        self.job_id = kwargs.get('_job', 123)
        self.callback = kwargs.get('callback', 'http://products.kuyun.loc/api/screen/shop')
        self.s_id = kwargs.get('s_id')
        self.title = ''
        self.seller_name = ''
        self.retry = 0  # 搜索店铺尝试次数
        self.logger.info(f'Received: {kwargs}')
        super().__init__(**kwargs)

    # 根据cookie获取token
    def get_token(self):
        cookie = self.rdb.rget()
        token = ''.join(re.findall('_m_h5_tk---([^;]+);', cookie)).split('_')[0]
        dict_cookies = dict([tuple(x.split('---')) for x in cookie.split(';')])
        return {'token': token, 'strcookie': cookie.replace('---', '='), 'dict_cookies': dict_cookies}

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

        data = {"id": 77, "shop_id": "107656986", "title": "转角1号精品女装店", "name": "美懒懒234", "platform_id": "3",
                "shop_link": "https://shop178139368.taobao.com/?spm=a230r.7195193.1997079397.240.26606459z5Rr9C",
                "callback": 'http://products.kuyun.loc/api/screen/shop', "token": "ce934bc118beedabd789ed5cf6a20dc7"}

        sid, title, seller_name, shop_id = (self.s_id, data.get('title'), data.get('name'), data.get('shop_id'))
        self.title, self.seller_name = title, seller_name
        yield scrapy.Request(url=self.baseurl + title,
                             cookies=self.dict_cookies, callback=self.parse_search,
                             meta={'sid': sid, 'shopid': shop_id})

    def test(self, response):
        cookie = self.get_token()
        # hd = copy.deepcopy(self.taobao_header)
        hd = self.taobao_header
        hd.update({'referer': None})
        n = response.meta.get('n')
        pdata = response.meta.get('pdata')
        print(f'test{n} cookie:', response.request.headers['Cookie'])

        data = re.sub('currentPage":\d+', 'currentPage":' + str(n), pdata)
        sign = self.sign(cookie.get('token'), self.appkeys, str(int(time.time() * 1000)), data)
        yield scrapy.Request(url=self.shopping_list.format(**sign), headers=hd,
                             cookies=cookie.get('dict_cookies'),
                             callback=self.shop_list_item, dont_filter=True,
                             meta={'pdata': data, 'request_tp': self.request_tp[0], 'pn': n,
                                   'cookiejar': response.meta.get('cookiejar')})

    def test1(self, response):
        n = response.meta.get('n')
        print(f'Test{n} cookie:', response.request.headers['Cookie'])

    # 搜索店铺信息并匹配
    def parse_search(self, response):
        print('first cookie:', response.request.headers['Cookie'])
        re_dt = {}
        shopid = response.meta.get('shopid')
        sid = response.meta.get('sid')
        doc = response.text.replace('&quot;', '"')
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
            yield scrapy.Request(url=self.baseurl + self.seller_name,
                                 cookies=self.dict_cookies, callback=self.parse_search,
                                 meta={'sid': sid, 'shopid': shopid})
            return
        if not re_dt and self.retry == 1:
            self.logger.error('final search title is failure!')
            return
        cookie = self.get_token()
        print('second cookie:', cookie.get('strcookie'))
        # hd = copy.deepcopy(self.taobao_header)
        # hd.update({'cookie': cookie.get('strcookie'), 'X-Crawlera-Cookies': 'disable'})
        header = {'X-Crawlera-Cookies': 'disable'}
        data = '{"sellerId": %s}' % re_dt.get('sellerid')
        st = self.sign(token=cookie.get('token'), appkey=self.appkeys, t=str(int(time.time() * 1000)), data=data)
        yield scrapy.Request(url=self.store_detail.format(**st), headers=header,
                             cookies=cookie.get('dict_cookies'), callback=self.parse_store_item,
                             meta={'re_data': json.dumps(re_dt), 'request_tp': self.request_tp[0]})

    # 进一步抓取店铺信息
    def parse_store_item(self, response):
        print('third cookie:', response.request.headers['Cookie'])
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

        pns = int(int(count) / 100) + 2
        cookie = self.get_token()
        # hd = copy.deepcopy(self.taobao_header)
        hd = self.taobao_header
        hd.update({'referer': None})
        # hd.update({'cookie': cookie.get('strcookie')})
        for pn in range(1, pns):
            self.cookie_used += 1
            # if self.cookie_used > 5:
            #     self.cookie_used = 0
            #     cookie = self.get_token()
            yield scrapy.Request(url=self.baseurl + self.seller_name,
                                 cookies=self.dict_cookies, callback=self.test,
                                 meta={'n': pn, 'pdata': pdata, 'cookiejar': pn}, dont_filter=True)
            data = re.sub('currentPage":\d+', 'currentPage":' + str(pn), pdata)
            sign = self.sign(cookie.get('token'), self.appkeys, str(int(time.time() * 1000)), data)
            # yield scrapy.Request(url=self.shopping_list.format(**sign), headers=hd,
            #                      cookies=cookie.get('dict_cookies'),
            #                      callback=self.shop_list_item, dont_filter=True,
            #                      meta={'pdata': data, 'request_tp': self.request_tp[0], 'pn': pn})

    # 按页抓取店铺里的商品列表
    def shop_list_item(self, response):
        pn = response.meta.get('pn')
        print(f'Cookie:{pn}', response.request.headers['Cookie'])
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
        # r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
        self.logger.info(f'length of all pids: {len(self.all_pids)}')
