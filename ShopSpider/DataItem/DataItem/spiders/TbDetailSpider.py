# -*- coding: utf-8 -*-

"""
抓取商品详情(暂时弃用)

"""

import logging
import re
import time
import datetime
import json
import requests
import scrapy

from random import randint
from DataItem.redis_pool import RedisPool
from DataItem.items import TbshopLoader, TbshopspiderItem
from DataItem.agent import item_list_hd, site_dict

from logging.handlers import RotatingFileHandler
from scrapy.selector import Selector

# from yundama_requests import YDMHttp

info_logger = logging.getLogger('cookie_error_log')
info_logger.setLevel(logging.DEBUG)
ch_info = RotatingFileHandler('get_cookie_info.log', maxBytes=10 * 1024 * 1024, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch_info.setFormatter(formatter)
info_logger.addHandler(ch_info)


class TbdetailspiderSpider(scrapy.Spider):
    name = 'TbDetailSpider'
    allowed_domains = ['*']
    logger = logging.getLogger('DetailSpider')
    logger.setLevel(logging.DEBUG)
    ch_info = RotatingFileHandler('sended.log', maxBytes=10 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch_info.setFormatter(formatter)
    logger.addHandler(ch_info)

    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 100,
        'DOWNLOADER_MIDDLEWARES': {
            'DataItem.middlewares.CMiddleware': 1,
        }
    }

    def __init__(self, **kwargs):
        # 初始化redis
        self.reds_conn = RedisPool().redis_con()
        self.reds_conn1 = RedisPool(db=4).redis_con()

        self.detail_api = ('https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?'
                           'data=%7B%22itemNumId%22%3A%22{0}%22%7D')

        # 初始化详情正则对象
        self.img_cpl = re.compile(r'.*?"img":"(https://.*?\.jpg)', re.DOTALL)  # 匹配详情图
        self.img_cpl2 = re.compile(r'.*?image":{"itemImages":\[(.*?)\].*', re.DOTALL)  # 匹配详情图
        self.desc_cpl = re.compile(r'.*?descUrl".*?"(.*?)"', re.DOTALL)  # 匹配详情图入口url
        self.all_imgs = []  # 所有图片的详情
        self.nostock = []  # 无货的商品列表
        self.error_urls = []
        self.job_id = kwargs.get('_job', 123)  # 此爬虫的job_id
        self.pre_job_id = kwargs.get('Shop_jobid', 123)  # 店铺列表爬虫的job_id
        self.callback = kwargs.get('callback', 'http://release.pl.kydev.org/api/screen/shop')
        self.s_id = kwargs.get('s_id', '')
        self.title = kwargs.get('title', '')
        self.tp = 0  # 0为新店采集,1为新品采集
        self.is_new = kwargs.get('is_new', False)
        if self.is_new:
            self.tp = 1
        self.shopid = kwargs.get('shopid', '')
        self.request_tp = ('store', 'detail')

        super().__init__(**kwargs)

    def start_requests(self):
        n = 0
        while True:
            n += 1
            resp = self.reds_conn.hget('_detail', self.pre_job_id)
            if resp or n > 500:
                break
            time.sleep(1)

        if resp:
            data = json.loads(resp)
        else:
            data = []

        self.logger.info(f'length of all prod: {len(data)}')

        for pid in data:
            url = self.detail_api.format(pid)
            yield scrapy.Request(url, callback=self.parse_tb, dont_filter=True, meta={'id': pid, 'u': url, 'slug': pid,
                                                                                      'request_tp': self.request_tp[1]})

    def parse_tb(self, response):
        resp = json.loads(response.text)
        data = resp['data']
        slug = response.meta.get('slug')  # 淘宝的商品ID

        if not resp.get('ret', ''):
            self.logger.error(f'failed: {response.request.url}')
            return

        # 无货
        if not data.get('item', ''):
            self.logger.error(f'no stock: {response.request.url}')
            self.nostock.append(slug)
            return

        # # 使用itemloader装载item, 暂弃用
        # item_loader = TbshopLoader(item=TbshopspiderItem())

        # 存放待发送商品详情信息的dict
        item_dict = dict()
        # 存放待发送店铺详情信息的dict
        shop_dict = dict()

        # 无货
        if not data.get('apiStack'):
            self.nostock.append(slug)
            self.logger.error(f'no stock: {response.request.url}')
            return
        try:
            price_info = json.loads(data['apiStack'][0]['value'])  # 价格信息
        except:
            self.logger.error(f'apiStack error: {response.request.url}')
            # print('apiStack', data.get('apiStack'))
            self.nostock.append(slug)
            return
        purchase_price = price_info['price']['price']['priceText'].split('-')[-1]  # 实际价格
        sell_count = price_info.get('item').get('sellCount') if price_info.get('item', dict()).get('sellCount') else 0
        addr = price_info.get('delivery').get('from') if price_info.get('delivery', dict()).get('from') else ''
        purchase_list_price = price_info['price'].get('extraPrices')
        purchase_list_price = purchase_list_price[0]['priceText'].split('-')[
            -1] if purchase_list_price else purchase_price  # 市场价

        seller_info = data['seller']  # 店家信息
        item = data['item']  # 商品信息
        skuBase = data['skuBase']
        option_values = skuBase.get('props', {})
        skubase_skus = skuBase.get('skus', '')  # sku信息
        skubase_props = skuBase.get('props', '')  # sku属性
        tmall_descurl = f"https:{item['tmallDescUrl']}"  # 商品图片详情页 origin
        module_descurl = f"https:{item['moduleDescUrl']}"  # 商品图片详情页 new
        images = item['images']  # 缩略图信息
        feature_image_list = [f'https:{u}' for u in images]
        prod_name = item['title']  # 商品名称
        site_type = data['params']['trackParams']['BC_type']  # B为天猫C为淘宝
        shop_id = seller_info['shopId']  # shopid
        nick = seller_info['sellerNick']  # shopid
        start = seller_info['starts']  # shopid
        try:
            props = data.get('props').get('groupProps')[0].get('基本信息')
        except:
            props = {}
        commentCount = item['commentCount']
        favcount = item['favcount']
        opt = [{'name': i['name'], 'values': [{'name': j['name'],
                                               'thumb': (f"http:{j.get('image')}" if not j.get('image').startswith(
                                                   'http') else j.get('image')) if j.get('image') else ''} for j in
                                              i['values']]} for i in option_values][::-1] if option_values else {}

        # 无sku信息则return
        # if not skubase_skus or not skubase_props:
        #     self.nostock.append(slug)
        #     self.logger.error(f'no sku: {response.request.url}')
        #     return

        # 商品源url
        if site_type == 'B':
            source_url = "https://detail.tmall.com/item.htm?id={0}".format(slug)
        else:
            source_url = "https://item.taobao.com/item.htm?id={0}".format(slug)
        source_url = [{"source_url": source_url}]

        sku_price_info = price_info['skuCore']['sku2info']  # sku价格
        stock = randint(1000, 10000)

        # 装载item,后面一样
        # item_loader.add_value('sel_price', purchase_price)  # true price--sel_price
        # item_loader.add_value('price', purchase_list_price)  # 市场价--price
        # item_loader.add_value('name', prod_name)  # 商品名--name
        # item_loader.add_value('stock', stock)  # 库存情况--stock
        # item_loader.add_value('source', source_url)  # 商品源信息--source
        # item_loader.add_value('item_id', slug)  # 商品ID--item_id
        # item_loader.add_value('shopid', shop_id)  # shopid--shopid
        # item_loader.add_value('props', props)  # 属性集--props
        # item_loader.add_value('reviews', commentCount)  # 评论数--reviews
        # item_loader.add_value('collects', favcount)  # 收藏数--collects
        # item_loader.add_value('options', opt)  # 选项集--options
        # item_loader.add_value('sells', sell_count)  # 销量--sells
        # item_loader.add_value('images', feature_image_list)  # 特色图集--images
        # item_loader.add_value('nick', nick)  # 特色图集--images
        # item_loader.add_value('start', start)  # 开店时间--start
        # item_loader.add_value('addr', addr)  # 发货地--addr

        item_dict.setdefault('sel_price', purchase_price)  # true price--sel_price
        item_dict.setdefault('price', purchase_list_price)  # 市场价--price
        item_dict.setdefault('name', prod_name)  # 商品名--name
        item_dict.setdefault('stock', stock)  # 库存情况--stock
        item_dict.setdefault('source', source_url)  # 商品源信息--source
        item_dict.setdefault('item_id', slug)  # 商品ID--item_id
        item_dict.setdefault('shopid', shop_id)  # shopid--shopid
        item_dict.setdefault('props', props)  # 属性集--props
        item_dict.setdefault('reviews', commentCount)  # 评论数--reviews
        item_dict.setdefault('collects', favcount)  # 收藏数--collects
        item_dict.setdefault('options', opt)  # 选项集--options
        item_dict.setdefault('sells', sell_count)  # 销量--sells
        item_dict.setdefault('images', feature_image_list)  # 特色图集--images
        # item_dict.setdefault('descr', '')
        shop_dict.setdefault('nick', nick)  # 昵称--nick
        shop_dict.setdefault('start', start)  # 开店时间--start
        shop_dict.setdefault('addr', addr)  # 发货地--addr
        shop_dict.setdefault('shopid', self.s_id)  # 产品库shopid--shopid

        # 抓取页面图片详情
        yield scrapy.Request(tmall_descurl,
                             callback=self.parse_detail,
                             meta={
                                 # 'item_loader': item_loader,
                                 'item_dict': item_dict, 'shop_dict': shop_dict,
                                 'skubase_skus': skubase_skus, 'slug': slug, 'no_crawlera': True,
                                 'skubase_props': skubase_props, 'sku_price_info': sku_price_info,
                                 'prod_name': prod_name, 'skuBase': skuBase, 'module_descurl': module_descurl},
                             dont_filter=True)

    #  解析详情接口,判断是否有图片接口存在,如果存在则进一步抓取图片
    def parse_detail(self, response):
        t = time.time()
        # item_loader = response.meta.get('item_loader')
        item_dict = response.meta.get('item_dict')
        shop_dict = response.meta.get('shop_dict')
        module_descurl = response.meta.get('module_descurl')
        data = response.text
        created_at = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        # item_loader.add_value('descr', data)
        # item_loader.add_value('created_at', created_at)
        item_dict.setdefault('descr', data)
        item_dict.setdefault('created_at', created_at)

        yield scrapy.Request(module_descurl,
                             callback=self.parse_img_new,
                             meta={
                                 # 'item_loader': item_loader,
                                 'item_dict': item_dict,
                                 'shop_dict': shop_dict,
                                 'no_crawlera': True
                             }, dont_filter=True)

        """
        # 另一种匹配详情图方式,性能较低暂弃用

        # img_match = self.img_cpl.findall(data)
        # if img_match:
        #     image_urls = img_match
        #     # 图片信息汇总
        #     self.all_imgs.append(str(len(image_urls)))
        #     print('1-1 deeps image_urls:', len(image_urls))
        #     item_loader.add_value('detail_images', image_urls)
        #     item_dict.setdefault('detail_images', image_urls)
        #     all_dict = {'shop': shop_dict, 'product': item_dict}
        #     print(all_dict)
        #     loader = item_loader.load_item()
        # yield loader

        """

        # # 判断是否有图片接口
        # if self.desc_cpl.match(data, re.DOTALL):
        #     detail_url = self.desc_cpl.match(data).group(1)
        #     detail_url = f'http:{detail_url}'
        #     if len(detail_url) > 1000:
        #         print(detail_url)
        #     yield scrapy.Request(detail_url, callback=self.parse_img_origin,
        #                          meta={
        #                              # 'item_loader': item_loader,
        #                              'item_dict': item_dict,
        #                              'shop_dict': shop_dict,
        #                              'request_tp': self.request_tp[1]
        #                          }, dont_filter=True)
        # else:
        #     self.logger.error(f'no img: {response.request.url}')
        #     return

    # 通过接口抓取图片
    def parse_img_origin(self, response):
        item_dict = response.meta.get('item_dict')
        shop_dict = response.meta.get('shop_dict')

        if "function(win,key)" in response.text:
            return scrapy.Request(response.request.url, callback=self.parse_img_origin,
                                  meta={'item_dict': item_dict, 'shop_dict': shop_dict, }, dont_filter=True)

        # item_loader = response.meta.get('item_loader')
        image_urls = response.css('img::attr(src)').extract()
        # item_loader.add_value('detail_images', image_urls)
        item_dict.setdefault('detail_images', image_urls)
        all_dict = {'shop': shop_dict, 'product': item_dict}
        self.reds_conn1.hset(self.title, item_dict['item_id'], json.dumps(all_dict, ensure_ascii=False))
        self.all_imgs.append(str(len(image_urls)))

        headers = site_dict[self.callback]['headers']
        cb = site_dict[self.callback]['url']
        if self.is_new:
            cb = cb.replace('product', 'news')
        data = json.dumps(all_dict)
        self.logger.warning(f'send_result: {data}')
        r = requests.post(cb, headers=headers, data=data, timeout=150)
        if r.status_code == 200:
            if r.json().get('status') == 200:
                self.logger.info(f'post success:{r.json(encoding="gbk")}')
            else:
                self.logger.info(f'post failed:{r.json(encoding="gbk")}')

        # loader = item_loader.load_item()
        # yield loader

    def parse_img_new(self, response):
        item_dict = response.meta.get('item_dict')
        shop_dict = response.meta.get('shop_dict')

        text = json.loads(response.text).get('data', {}).get('children')
        image_urls = list()
        if text:
            for detail in text:
                img = detail.get('params', {}).get('picUrl')
                if img:
                    image_urls.append(img)
        if not image_urls:
            self.logger.error(f'no img: {response.request.url}')
        item_dict.setdefault('detail_images', image_urls)
        all_dict = {'shop': shop_dict, 'product': item_dict}
        self.reds_conn1.hset(self.title, item_dict['item_id'], json.dumps(all_dict, ensure_ascii=False))
        self.all_imgs.append(str(len(image_urls)))

        headers = site_dict[self.callback]['headers']
        cb = site_dict[self.callback]['url']
        if self.is_new:
            cb = cb.replace('product', 'news')
        data = json.dumps(all_dict)
        self.logger.warning(f'send_result: {data}')
        r = requests.post(cb, headers=headers, data=data, timeout=150)
        if r.status_code == 200:
            if r.json().get('status') == 200:
                self.logger.info(f'post success:{r.json(encoding="gbk")}')
            else:
                self.logger.info(f'post failed:{r.json(encoding="gbk")}')

        # loader = item_loader.load_item()
        # yield loader

    def close(self, spider, reason):
        self.logger.info(f'len all imgs: {len(self.all_imgs)}')
        self.logger.info(f'urls error: {len(self.error_urls)}')
        self.logger.info(f'no stock: {len(self.nostock)}')
        url = site_dict[self.callback]['result']
        data = json.dumps({'shopid': self.s_id, 'num': len(self.all_imgs), 'type': self.tp})
        self.logger.warning(f'send_result: {data}')
        r = requests.post(url, data=data, headers=site_dict[self.callback]['headers'])
        self.logger.info(f'{r.text}')
