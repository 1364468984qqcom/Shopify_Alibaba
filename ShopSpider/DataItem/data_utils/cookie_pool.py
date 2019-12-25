#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/22 12:02
# @Author  : zhangpeng
# @File    : cookie_pool.py
# 说明     :  生成cookie池


import time
import redis
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class CreateCookie(object):

    def __init__(self):
        self.T = 3000  # 过期时间
        self.save_key = 'logout_cookie'
        self.website = 'https://h5.m.taobao.com/'
        self.redis_conn = redis.Redis(host='127.0.0.1', port=6379, db=0)
        # self.driver = self.init_drive()

    def init_drive(self):
        for i in range(0, 3):
            try:
                # 设置成手机模式
                mobile_emulation = {"deviceName": "iPhone X"}
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument("window-size=2436, 1125")
                options.add_argument("--no-sandbox")
                options.add_argument("disable-infobars")
                # 去除自动化框
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_argument('log-level=3')

                options.add_experimental_option("mobileEmulation", mobile_emulation)
                options.add_argument(
                    'user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"')

                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(5)
                driver.set_script_timeout(5)
                return driver
            except Exception as e:
                print(e)
                continue
        return

    def get_cookie_by_PhantomJS(self, domain):
        for i in range(0, 3):
            driver = self.init_drive()
            try:
                driver.get(domain)
                time.sleep(0.5)
                cookies = driver.get_cookies()
                cookie = [item["name"] + "=" + item["value"] for item in cookies]
                cookiestr = ';'.join(item for item in cookie)  # 将每一个cookie的值都用;隔开
                return cookiestr
            except Exception as e:
                print(e)
                continue
            finally:
                driver.quit()
        return

    def create_cookies(self):
        while True:
            cookie = self.get_cookie_by_PhantomJS(self.website)
            if cookie:
                self.redis_conn.lpush(self.save_key, cookie)  # 将cookie储存在redis的列表里面
            else:
                print('cookie create is error!')
            time.sleep(15)

    # 设置cookie的时效
    def set_time_cookie(self):
        cookie = self.get_cookie_by_PhantomJS(self.website)
        if cookie:
            self.redis_conn.lpush(self.save_key, cookie)
            self.redis_conn.ltrim(self.save_key, 0, 350)  # 只保持351个元素在redis列表里面，并且删除多余的
            return cookie
        else:
            print('cookie create is error!')
            return None


if __name__ == "__main__":
    # c = CreateCookie()
    # while c.redis_conn.llen(c.save_key) == 0:
    #     c.set_time_cookie()
    schedule.every(1).seconds.do(CreateCookie().set_time_cookie)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            continue
    # cc = CreateCookie()
    # # cc.create_cookies()
    # cc.set_time_cookie()
