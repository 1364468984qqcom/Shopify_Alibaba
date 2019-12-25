# -*- coding: utf-8 -*-

import json
import redis
import requests
from flask import Flask, request
from scrapy import Selector

app = Flask(__name__)
TOKEN = 'ce934bc118beedabd789ed5cf6a20dc7'
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=0)


@app.route('/request_crawler', methods=["POST"])
def request_crawler():
    if request.method == 'POST':
        params = json.loads(request.get_data(as_text=True))
        data = params.get('data')
        url = data.get('url')
        reds = redis.Redis(connection_pool=pool)
        if url:
            r = requests.get(url)
            s = Selector(text=r.text)
            shopId = s.css('#LineZing::attr(shopid)').get()
            if 'taobao' in url:
                if s.css('.hd-shop-name a::text').get():
                    shopName = s.css('.hd-shop-name a::text').get()
                elif s.css('.first-block .shop-name span::text').get():
                    shopName = s.css('.first-block .shop-name span::text').get()
                else:
                    shopName = ''

                if s.css('.tb-box-half.tb-seller-info label::text').get():
                    sellerName = s.css('.tb-box-half.tb-seller-info label::text').get().strip()
                elif s.css('.seller-name::text').get():
                    sellerName = s.css('.seller-name::text').get().strip('掌柜：')
                elif s.css('.shop-more-info p.info-item:nth-child(2)::text').get():
                    sellerName = s.css('.shop-more-info p.info-item:nth-child(2)::text').get().strip()
                else:
                    sellerName = ''

            elif 'tmall' in url:
                if s.css('.hd-shop-name a::text').get():
                    shopName = s.css('.hd-shop-name a::text').get()
                else:
                    shopName = s.css('.slogo-shopname strong::text').get()
                if s.css('.tb-box-half.tb-seller-info label::text').get():
                    sellerName = s.css('.tb-box-half.tb-seller-info label::text').get().strip()
                else:
                    sellerName = s.css('.shopkeeper div a::text').get()
            else:
                shopName, sellerName = '', ''
            shopInfo = {'shopname': shopName, 'shopid': shopId, 'sellername': sellerName}
            reds.hset('_ShopInfoQuery', json.dumps(shopInfo, ensure_ascii=False), url)
            return json.dumps({'code': 200, 'msg': 'success', 'shop_info': shopInfo}, ensure_ascii=False)
        elif data:
            post_data = dict()
            callback = data.get('callback')
            s_id = data.get('id')
            sort_type = data.get('sort_type', '_sale')
            if not callback:
                return json.dumps({'code': 400, 'msg': 'wrong callback'})
            post_data['project'] = 'DataItem'
            # post_data['spider'] = 'TbShopSpider'
            # post_data['spider'] = 'NewTbShopSpider'
            post_data['spider'] = 'TbShopSpider'
            # post_data['spider'] = 'TbShopSpider_logout_new'
            post_data['callback'] = callback
            post_data['s_id'] = s_id
            post_data['sort_type'] = sort_type
            r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
            jobid = r.json()['jobid']
            print(jobid)
            reds.hset('_all_shop', data.get('id'), json.dumps(data, ensure_ascii=False))
            reds.hset('store', jobid, json.dumps(data, ensure_ascii=False))
            return json.dumps({'code': 200, 'msg': 'success'})
        else:
            return json.dumps({'code': 500, 'msg': 'failure'})


@app.route('/recieve_cookie', methods=["POST"])
def recieve_cookie():
    if request.method == 'POST':
        params = json.loads(request.get_data(as_text=True))
        data = params.get('data')
        cookie = data.get('cookie')
        nick = data.get('nick')
        reds = redis.Redis(connection_pool=pool)
        reds.hset('queue_cookie', nick, cookie)
        return json.dumps({'code': 200, 'msg': 'success'})
    else:
        return json.dumps({'code': 500, 'msg': 'failure'})




@app.route('/video_crawl', methods=["POST"])
def video_crawl():
    if request.method == 'POST':
        params = json.loads(request.get_data(as_text=True))
        data = params.get('data')
        callback = data.get('callback')
        reds = redis.Redis(connection_pool=pool)
        post_data = dict()
        post_data['project'] = 'DataItem'
        post_data['spider'] = 'VideoSpider'
        post_data['callback'] = callback
        r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
        jobid = r.json()['jobid']
        print(jobid)
        reds.hset('video', jobid, json.dumps(data, ensure_ascii=False))
        reds.expire('video', 15000)
        return json.dumps({'code': 200, 'msg': 'success'})
    else:
        return json.dumps({'code': 500, 'msg': 'failure'})


@app.before_request
def before_request():
    if request.method == 'POST':
        jdata = json.loads(request.get_data(as_text=True)).get('data', dict())
        if jdata.get('token') and TOKEN == jdata.get('token'):
            pass
        else:
            return json.dumps({'code': 403, 'msg': 'invalid token'})

    elif request.method == 'GET':
        params = str(request.url)
        if '?' in params and 'token=' + TOKEN in params.split('?')[-1]:
            pass
        else:
            return json.dumps({'code': 403, 'msg': 'invalid token'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
