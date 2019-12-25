import json
import time

import redis
import requests
from urllib import parse
from selenium import webdriver
from selenium.webdriver.chrome import options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def get_cookie():
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=0)
    Reds = redis.Redis(connection_pool=pool)
    option = options.Options()
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    browser = webdriver.Chrome(options=option)
    browser.get('https://login.taobao.com')
    browser.maximize_window()
    # browser.switch_to.frame(0)
    browser.find_element_by_css_selector('#J_Quick2Static').click()
    browser.find_element_by_css_selector('#TPL_username_1').send_keys('18729360524')
    browser.find_element_by_css_selector('#TPL_password_1').send_keys('x5f0c9v5q')
    browser.find_element_by_css_selector('#J_SubmitStatic').click()
    css_locator = '#J_SiteNavMytaobao .site-nav-menu-hd a span'
    locator = (By.CSS_SELECTOR, css_locator)
    WebDriverWait(browser, 20000, 0.5).until(EC.presence_of_element_located(locator))
    browser.get('https://h5.m.taobao.com/')
    time.sleep(3)
    cookies = browser.get_cookies()
    cookie = []
    nick = ''
    for item in cookies:
        cookie.append(item["name"] + "=" + item["value"])
        if item["name"] == '_nk_':
            nick = parse.unquote(item["value"])
    nick = json.loads(f'"{nick}"')
    cookiestr = ';'.join(item for item in cookie)
    Reds.hset('queue_cookie', nick, cookiestr)
    browser.quit()


if __name__ == '__main__':
    # get_cookie(url='http://154.223.183.141:8888/recieve_cookie')
    # with open
    get_cookie()
