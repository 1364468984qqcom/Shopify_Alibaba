import time
import schedule
from scrapy.cmdline import execute
import subprocess
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

"""
此文件为主调试入口,flask接口文件是 /api/start_spider.py
"""


def start():
    # subprocess.Popen('scrapy crawl Taobao')
    # execute(['scrapy', 'crawl', 'store_shopping'])
    # execute(['scrapy', 'crawl', 'shopping_list'])
    # execute(['scrapy', 'crawl', 'all_spider'])
    # execute(['scrapy', 'crawl', 'TbShopSpider'])
    execute(['scrapy', 'crawl', 'TbShopSpider_logout_app'])
    # execute(['scrapy', 'crawl', 'TbShopSpider_logout_new'])
    # execute(['scrapy', 'crawl', 'TbShopSpider1'])
    # execute(['scrapy', 'crawl', 'NewTbShopSpider'])
    # execute(['scrapy', 'crawl', 'TbDetailSpider'])
    # execute(['scrapy', 'crawl', 'TbDetailSpiderNew'])
    # execute(['scrapy', 'crawl', 'VideoSpider'])


start()
# schedule.every().day.at("20:00").do(start)
# while True:
#     schedule.run_pending()
#     time.sleep(1)
