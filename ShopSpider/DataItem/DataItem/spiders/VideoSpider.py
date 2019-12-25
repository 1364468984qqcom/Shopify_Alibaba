# -*- coding: utf-8 -*-

"""
抓取视频链接

"""

import json
import logging
import re
import time
import scrapy_redis
import requests
import scrapy
from DataItem.redis_pool import RedisPool
from DataItem.agent import item_list_hd, site_dict


class VideoSpider(scrapy.Spider):
    name = 'VideoSpider'
    allowed_domains = ['*']
    start_urls = ['http://VideoSpider/']
    logger = logging.getLogger('VideoSpider')

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36',
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'DataItem.middlewares.CMiddleware': 1,
        # }
    }

    def __init__(self, *args, **kwargs):
        self.result = []
        self.tb_url = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?data=%7B%22itemNumId%22%3A%22{0}%22%7D'
        self.tm_url = 'https://detail.tmall.com/item.htm?id={0}'
        self.rdb = RedisPool()
        self.reds_conn = self.rdb.redis_con()
        self.job_id = kwargs.get('_job', 123)  # 此爬虫的job_id
        self.cb = kwargs.get('callback', 123)  # 此爬虫的job_id
        self.logger.warning(f'kwargs: {kwargs}')
        super().__init__(*args, **kwargs)

    def start_requests(self):
        n = 0
        while True:
            n += 1
            resp = self.reds_conn.hget('video', self.job_id)
            if resp or n > 50:
                break
            time.sleep(1)

        if resp:
            data = json.loads(resp)
        else:
            return
        self.logger.info(f'recieved: {data}')

        # data = {'token': 'ce934bc118beedabd789ed5cf6a20dc7',
        #         'callback': 'http://release.pl.kydev.org/api/screen/receive-video',
        #         'products': [{'platform_id': 3, 'origin_id': '595039642463', 'product_id': 495232}]}
        # data = {'token': 'ce934bc118beedabd789ed5cf6a20dc7',
        #         'callback': 'http://release.pl.kydev.org/api/screen/receive-video',
        #         'products': [{'platform_id': 33, 'origin_id': 17457109, 'product_id': ''}]}
        ids_info = data.get('products')

        for id_info in ids_info:
            platform_id = id_info['platform_id']
            origin_id = id_info['origin_id']
            product_id = id_info['product_id']
            if int(id_info['platform_id']) == 3:
                yield scrapy.Request(url=self.tb_url.format(origin_id),
                                     callback=self.parse_tb,
                                     meta={'product_id': product_id, 'origin_id': origin_id, 'request_tp': 'detail'},
                                     dont_filter=True)
            if int(id_info['platform_id']) == 4:
                yield scrapy.Request(url=self.tm_url.format(origin_id),
                                     callback=self.parse_tm,
                                     meta={'product_id': product_id, 'origin_id': origin_id},
                                     dont_filter=True)

        # sid, title, seller_name, shop_id = (self.s_id, data.get('title'), data.get('name'), data.get('shop_id'))

    def parse_tb(self, response):
        product_id = response.meta.get('product_id')
        origin_id = response.meta.get('origin_id')
        resp = json.loads(response.text)
        data = resp.get('data')
        video_info = {
            "platform_id": "3",
            "origin_id": origin_id,
            "product_id": product_id
        }
        if not data.get('apiStack'):
            video_info['video_link'] = ''
            self.result.append(video_info)
            return
        try:
            prod_info = json.loads(data['apiStack'][0]['value'])
            video_url = prod_info.get('item', dict()).get('videos', list())[0].get('url', '')
            video_info['video_link'] = video_url
        except:
            video_info['video_link'] = ''
        finally:
            self.result.append(video_info)

    def parse_tm(self, response):
        product_id = response.meta.get('product_id')
        origin_id = response.meta.get('origin_id')
        video_info = {
            "platform_id": "3",
            "origin_id": origin_id,
            "product_id": product_id
        }
        try:
            # self.logger.warning(f'{response.text}')
            re_match = re.match(
                r'.*?imgVedioID.*?(\d+).*?userId.*?(\d+).*|.*?"userId.*?(\d+).*?videoId.*?(\d+).*', response.text,
                re.DOTALL).groups()
            video_id, user_id = re_match[:2] if re_match[0] else re_match[::-1][:2]
            video_url = f'https://cloud.video.taobao.com/play/u/{user_id}/p/1/e/6/t/1/{video_id}.mp4'
            video_info['video_link'] = video_url
        except:
            video_info['video_link'] = ''
        finally:
            self.result.append(video_info)

    def close(self, spider, reason):
        self.logger.warning(f'result:{self.result}')
        headers = site_dict[self.cb]['headers']
        r = requests.post(self.cb, data=json.dumps(self.result), headers=headers)
        self.logger.warning(f'status_code :{r.status_code}')
        self.logger.warning(f'resp :{r.text}')


