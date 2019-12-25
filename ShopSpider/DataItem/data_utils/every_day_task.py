import json
import time
import redis
import schedule
import requests

from datetime import datetime


def redis_task():
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=0)
    reds = redis.Redis(connection_pool=pool)
    all_shop = reds.hgetall('_all_shop')
    for data in all_shop:
        shop_info = json.loads(all_shop.get(data, dict()))
        post_data = dict()
        post_data['project'] = 'DataItem'
        post_data['spider'] = 'TbShopSpider'
        post_data['callback'] = shop_info.get('callback')
        post_data['s_id'] = data
        post_data['sort_type'] = 'first_new'
        r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=50)
        print(data, r.text)
    print(datetime.now())


def req_task():
    r = requests.get(
        # 'http://release.pl.kydev.org/api/screen/list',
        'http://pl.kydev.org/api/screen/list',
        headers={
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        })

    all_data = r.json()
    for shop_info in all_data:
        sid = shop_info.get('id')
        post_data = dict()
        post_data['project'] = 'DataItem'
        post_data['spider'] = 'TbShopSpider_logout_new'
        post_data['callback'] = 'http://pl.kydev.org/api/screen/shop'
        # post_data['callback'] = 'http://release.pl.kydev.org/api/screen/shop'
        post_data['s_id'] = sid
        r = requests.post('http://localhost:6800/schedule.json', data=post_data, timeout=11)
        print(sid, r.text)
    print(datetime.now())


if __name__ == "__main__":
    req_task()
    schedule.every().day.at("00:00").do(req_task)
    schedule.every().day.at("12:00").do(req_task)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            continue
