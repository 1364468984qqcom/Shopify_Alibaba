# -*- coding: utf-8 -*-

"""
使用页面直取获取店铺列表

"""

import logging
import copy
import re
import time
import hashlib
import json
from html import unescape

import requests
import scrapy
from scrapy import signals

from scrapy.selector import Selector
from DataItem.DataItem.redis_pool import RedisPool
from DataItem.DataItem.agent import item_list_hd, site_dict, cookie1


class TbshopspiderSpider(scrapy.Spider):
    name = 'NewTbShopSpider'
    allowed_domains = ['taobao.com', 'tmall.com']
    redis_key = "all_spider:strat_urls"
    logger = logging.getLogger('ShopSpider')
    cookie_used = 0
    cookies = ''

    custom_settings = {
        # 'CRAWLERA_ENABLED': False
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 1
    }

    def __init__(self, **kwargs):
        # 初始化redis
        self.rdb = RedisPool()
        self.reds_conn = self.rdb.redis_con()

        # 初始化请求类别, 用于区别代理
        self.request_tp = ('store', 'detail')

        # 初始化url
        self.store_list = '/i/asynSearch.htm?mid=w-{0}-0&pageNo='
        # self.store_list = 'https://shop{0}.taobao.com/i/asynSearch.htm?callback=jsonp58&mid=w-15676986376-0&wid=15676986376&pageNo={1}&path=/search.htm&search=y'
        self.baseurl = 'http://shop.m.taobao.com/shop/shopsearch/search_page_json.do?sort=default&type=all&q='
        self.store_detail = ('http://h5api.m.taobao.com/h5/mtop.taobao.geb.shopinfo.queryshopinfo/2.0/?jsv=2.4.2'
                             '&appKey={appkey}&t={t}&sign={sign}&api=mtop.taobao.geb.shopinfo.queryshopinfo&v=2.0'
                             '&type=originaljson&timeout=3000&AntiCreep=true&dataType=json&H5Request=true&data={data}')

        self.appkeys = '12574478'
        self.cookie_token = self.get_token()
        if self.cookie_token:
            ctk = self.cookie_token[-1]
            self.h5_token = ctk.get('token')
            self.cookie = ctk.get('strcookie')
            self.dict_cookies = ctk.get('dict_cookies')
            self.taobao_header = item_list_hd
            self.taobao_header.update({'cookie': self.cookie})

        # 初始化详情正则对象
        self.all_pids = []
        self.job_id = kwargs.get('_job', 123)
        self.callback = kwargs.get('callback', 'http://products.kuyun.loc/api/screen/shop')
        self.s_id = kwargs.get('s_id')
        self.title = ''
        self.seller_name = ''
        self.shop_id = 0
        self.retry = 0  # 搜索店铺尝试次数
        self.logger.info(f'Received: {kwargs}')
        self.fail_urls = []
        super().__init__(**kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.crawl_failed, signals.spider_closed)
        return spider

    def crawl_failed(self):
        self.crawler.stats.set_value('Failed Urls', json.dumps(self.fail_urls))

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

        # data = {
        #     'id': '10086',
        #     'title': '优衣库官方旗舰店',
        #     'shop_id': '57303596',
        #     'name': '优衣库官方旗舰店',
        # }
        data = {
            'id': '10086',
            'title': '沐乃衣女装',
            'shop_id': '33495993',
            'name': 'xvsh_007',
            'shop_link': 'https://shop33495993.taobao.com/?spm=a230r.7195193.1997079397.175.775317c5lQR0Am'
        }

        sid, self.title, self.seller_name, self.shop_id, shop_link = self.s_id, data.get('title'), data.get(
            'name'), data.get('shop_id'), data.get('shop_link')

        if 'tmall.com' in shop_link:
            u = re.match('(.*tmall\.com?).*', shop_link).group(1)
            r = requests.get(f'{u}/search.htm')
            sel = Selector(text=r.text)
            wid = sel.css('[data-title=搜索列表]::attr(data-widgetid)').get()
            self.store_list = f'{u}{self.store_list.format(wid)}'

        elif 'taobao.com' in shop_link:
            u = re.match('(.*taobao\.com?).*', shop_link).group(1)
            r = requests.get(f'{u}/search.htm')
            sel = Selector(text=r.text)
            wid = sel.css('[data-title=宝贝列表]::attr(data-widgetid)').get()
            self.store_list = f'{u}{self.store_list.format(wid)}'

        else:
            return
        yield scrapy.Request(url=self.baseurl + self.title, callback=self.parse_search,
                             meta={'sid': sid, 'shopid': self.shop_id})

    def get_pids(self, response):
        text = response.text.replace('\\"', '').replace('\\', '')
        s = Selector(text=text)
        firstPagePids = s.css('.J_TItems div .item::attr(data-id)').getall()
        pids = firstPagePids[:len(firstPagePids) - 10]
        if not pids:
            self.fail_urls.append(response.request.url)
            self.logger.warning('ShopList Crawl Failed')
        self.all_pids.extend(pids)

    def get_token(self):
        cookie_info = self.rdb.hgetall('queue_cookie')
        cookie_list = []
        for cookie in cookie_info:
            # login_cookie = cookie_info[list(cookie_info)[int(self.s_id) % len(cookie_info)]]  # 循环取cookie
            token = ''.join(re.findall('_m_h5_tk=([^;]+);', cookie_info[cookie])).split('_')[0]
            dict_cookies = dict([tuple(x.split('=', 1)) for x in cookie_info[cookie].split(';')])
            cookie_list.append({'token': token, 'strcookie': cookie_info[cookie], 'dict_cookies': dict_cookies})
        return cookie_list

    # 根据所需元素计算sign
    def sign(self, token, appkey, t, data):
        pp = '&'.join([token, t, appkey, data]).encode()
        sign = hashlib.md5(pp).hexdigest()
        return {'sign': sign, 't': t, 'appkey': appkey, 'data': data}

    def parse_pages(self, response):
        count = response.meta.get('count', 0)
        text = response.text.replace('\\"', '').replace('\\', '')
        s = Selector(text=text)
        pages = s.css('.ui-page-s-len::text').get()
        try:
            totalPages = int(pages.split('/')[-1])
        except:
            totalPages = int(count / 40)
        self.get_pids(response)
        # for page in range(1, totalPages + 1):
        for page in range(1, totalPages + 1):
            url = f'{self.store_list}{page}'
            cookie = self.cookie_token[page % len(self.cookie_token)].get('strcookie')
            print(page, ':', url)
            print('cookie:', cookie)
            headers = {
                'cookie': cookie,
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
            }
            time.sleep(5)
            r = requests.get(url, headers=headers)
            self.get_pids(r)
            # yield scrapy.Request(url=url, cookies=self.cookies, callback=self.parse, headers={'cookie': cookie},)

    def parse(self, response):
        self.get_pids(response)

    # 搜索店铺信息并匹配
    def parse_search(self, response):
        re_dt = {}
        shopid = response.meta.get('shopid')
        sid = response.meta.get('sid')
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
                                 meta={'sid': sid, 'shopid': shopid, 'request_tp': self.request_tp[1]})
        if not re_dt and self.retry == 1:
            self.logger.error('final search title is failure!')
            return
        cookie = self.cookie_token[-1]
        hd = copy.deepcopy(self.taobao_header)
        hd.update({'cookie': cookie.get('strcookie')})
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

        cookies = self.cookie_token[0]
        cookie = cookies.get('strcookie')
        # time.sleep(2)
        yield scrapy.Request(url=f'{self.store_list}1', headers={'cookie': cookie},
                             cookies=cookies.get('dict_cookies'), callback=self.parse_pages, meta={'count': count})

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
        r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
        self.logger.info(f'length of all pids: {len(self.all_pids)}')
