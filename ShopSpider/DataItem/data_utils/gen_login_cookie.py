import json
import time
import traceback
from io import BytesIO

import redis
import requests
import schedule
import random
import logging

from PIL import Image
from urllib import parse
from selenium.webdriver.chrome import options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from logging.handlers import RotatingFileHandler
from scrapy.selector import Selector
from yundama_requests import YDMHttp

cookie_error_logger = logging.getLogger('cookie_error_log')
cookie_info_logger = logging.getLogger('cookie_info_log')
cookie_error_logger.setLevel(logging.WARNING)
cookie_info_logger.setLevel(logging.DEBUG)
ch_error = RotatingFileHandler('get_cookie_error.log', maxBytes=3 * 1024 * 1024, backupCount=1)
ch_info = RotatingFileHandler('get_cookie_info.log', maxBytes=10 * 1024 * 1024, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch_error.setFormatter(formatter)
ch_info.setFormatter(formatter)
cookie_error_logger.addHandler(ch_error)
cookie_info_logger.addHandler(ch_info)


def get_cookie(account, yundama):
    """
    使用微博关联登陆淘宝,进而从m端淘宝页面获取cookie
    """
    username = account.get('username')
    password = account.get('password')
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True, db=0)
    reds = redis.Redis(connection_pool=pool)
    option = options.Options()
    option.add_argument("disable-infobars")
    # 去除自动化框
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('log-level=3')
    # option.add_argument("--proxy-server=http://114.239.254.76:4236")
    # option.add_argument('--headless')
    # option.add_argument("window-size=2436, 1125")
    # option.add_argument("--no-sandbox")

    browser = webdriver.Chrome(options=option)
    browser.implicitly_wait(20)
    try:
        browser.get('https://weibo.com/')
        browser.maximize_window()
        # 等待微博登录框加载完成后输入账号密码登陆
        wb_locator = '.login_innerwrap .W_login_form[node-type=normal_form] input[name=username]'
        WebDriverWait(browser, 300, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, wb_locator)))
        browser.find_element_by_css_selector('.login_innerwrap [node-type=normal_form] input[name=username]').send_keys(
            username)
        browser.find_element_by_css_selector('.login_innerwrap [node-type=normal_form] input[name=password]').send_keys(
            password)
        time.sleep(3)

        n = 0
        while True:
            sel = Selector(text=browser.page_source)
            verify_img = sel.css('[action-type=btn_change_verifycode]::attr(src)').get()
            if not verify_img:
                try:
                    browser.find_element_by_css_selector('.login_innerwrap [node-type=normal_form] .W_btn_a').click()
                except:
                    break
                break
            if verify_img != 'about:blank' and n < 6:
                img_content = requests.get(verify_img).content
                # img = Image.open(BytesIO(img_content))
                # img.show()
                verify = verifycode(yundama, img_content)
                browser.find_element_by_css_selector('[value=验证码]').send_keys(verify)
                browser.find_element_by_css_selector('.login_innerwrap [node-type=normal_form] .W_btn_a').click()
                time.sleep(5)
                n += 1
            else:
                browser.find_element_by_css_selector('.login_innerwrap [node-type=normal_form] .W_btn_a').click()
                break

        # 等待微博登陆完成后转到淘宝登陆页面并点击使用微博登陆
        wb_login_locator = '.WB_feed_detail'
        WebDriverWait(browser, 300, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, wb_login_locator)))
        browser.get('https://login.taobao.com')
        try:
            browser.find_element_by_css_selector('#J_Quick2Static').click()
        except:
            pass
        browser.find_element_by_css_selector('.weibo-login').click()

        # 判断是否有微博快速登录框出现,有则点击,无则输入微博密码登陆
        if browser.find_element_by_css_selector('.logged_info .W_btn_g'):
            # tb_submit_locator = '.logged_info .W_btn_g'
            # WebDriverWait(browser, 300, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, tb_submit_locator)))
            browser.find_element_by_css_selector('.logged_info .W_btn_g').click()
        elif browser.find_elements_by_css_selector('[node-type=submitStates]'):
            return
            browser.find_element_by_css_selector('.enter_psw').send_keys(password)
            browser.find_element_by_css_selector('[node-type=submitStates]').click()

        # 等待淘宝登陆完成后转入淘宝m端首页
        tb_locator = '.logo-bd'
        WebDriverWait(browser, 300, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, tb_locator)))
        browser.get('https://h5.m.taobao.com')

        # 等待淘宝m端首页加载完成,获取cookie并存入redis
        m_tb_locator = '.header-bd'
        WebDriverWait(browser, 300, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, m_tb_locator)))
        cookies = browser.get_cookies()
        cookie = []
        nick = ''
        for item in cookies:
            cookie.append(item["name"] + "=" + item["value"])
            if item["name"] == '_nk_':
                nick = parse.unquote(item["value"])
        nick = json.loads(f'"{nick}"')
        cookiestr = ';'.join(item for item in cookie)
        reds.hset('queue_cookie', nick, cookiestr)
        cookie_info_logger.debug(f'{nick}: {cookiestr}')
        # time.sleep(100)
        browser.quit()
        url = 'http://154.223.183.141:8888/recieve_cookie'
        r = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(
            {'data': {'cookie': cookiestr, 'nick': nick, "token": "ce934bc118beedabd789ed5cf6a20dc7"}}))
        print(r.text)

    except Exception as e:
        cookie_error_logger.error(f'cookie获取失败: {e}', exc_info=True)
        # browser.quit()


def verifycode(yundama, image_content):
    codetype = '1005'
    timeout = 60
    uid = yundama.login()
    balance = yundama.balance()
    print('balance: %s' % balance)
    # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
    cid, result = yundama.decode(image_content, codetype, timeout)
    print('cid: %s, result: %s' % (cid, result))
    return result


# 三个账号循环获取cookie
def main(yundama):
    accounts = [
        # {"username": 18729360524, "password": "x5f0c9v5q"},
        {"username": 15339179726, "password": "syt123"},
        # {"username": 13032961381, "password": "xfs2e8mygnsa"},
        # {"username": 18009255076, "password": "syt123"},
        # {"username": 18729204241, "password": "syt123"},

        # {"username": 15529521935, "password": "syt123"},
        # {"username": 18092485325, "password": "syt123"},
        # {"username": 15102908761, "password": "syt123"},
        # {"username": 18729974244, "password": "syt123"},

        # {"username": 15289285150, "password": "syt123"},

        # {"username": 13022812193, "password": "syt123"},
        # {"username": 18729046524, "password": "syt123"},
        # {"username": 15339107852, "password": "syt123"},
        # {"username": 15339179726, "password": "syt123"},
        # {"username": 18729360524, "password": "syt123"},
    ]
    # 加入随机等待时间减少被反爬识别概率
    for account in accounts:
        number = random.uniform(10, 300)
        time.sleep(number)
        try:
            get_cookie(account, yundama)
        except:
            continue


if __name__ == '__main__':
    username = 'scrapy_yun_zjc'
    password = '123456'
    appid = '7309'
    appkey = '15b3e5e8c3004bcea8db86eaed3266b9'
    # 验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
    yundama = YDMHttp(username, password, appid, appkey)
    # yundama = 1

    main(yundama)
    schedule.every(75).minutes.do(main, yundama)
    while True:
        schedule.run_pending()
        time.sleep(3)
