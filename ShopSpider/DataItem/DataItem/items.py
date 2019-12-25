# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import json
import scrapy
from scrapy.loader import ItemLoader


def trans_to_json(value):
    return json.dumps(value)


class TbshopspiderItem(scrapy.Item):
    sel_price = scrapy.Field()
    price = scrapy.Field()
    name = scrapy.Field()
    stock = scrapy.Field()
    source = scrapy.Field()
    item_id = scrapy.Field()
    shopid = scrapy.Field()
    props = scrapy.Field()
    reviews = scrapy.Field()
    collects = scrapy.Field()
    options = scrapy.Field()
    sells = scrapy.Field()
    images = scrapy.Field()
    descr = scrapy.Field()
    detail_images = scrapy.Field()
    created_at = scrapy.Field()
    nick = scrapy.Field()
    start = scrapy.Field()
    addr = scrapy.Field()


class TbshopLoader(ItemLoader):
    pass
