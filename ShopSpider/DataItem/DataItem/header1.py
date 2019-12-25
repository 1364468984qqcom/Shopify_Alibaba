# -*- coding: utf-8 -*-


import requests
import json
d = {
    "id": 487,
    "shop_id": "114461749",   #店铺id
    "title": "lrud旗舰店",   #店铺名称
    "name": "lrud旗舰店",   #掌柜名称
    "platform_id": 4,    #产品库定义的平台ID,淘宝为3,天猫为4
    "shop_link": "https://lrud.tmall.com/?spm=a1z10.3-b-s.1997427721.d4918089.3b744ec9ReRSry",   #店铺链接
    "callback": "http://xxx.com/api/screen/shop",   #发送采集结果的回调地址
    "token": "ce934bc118beedabd789ed5cf6a20dc7"   #接口请求认证
}
r = requests.post('http://host:port/request_crawler',
                  headers={"Content-Type": "application/json"},
                  data=json.dumps({'data': d}))

