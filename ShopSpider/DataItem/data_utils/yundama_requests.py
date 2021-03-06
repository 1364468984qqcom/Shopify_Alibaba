import json
import time
import requests


class YDMHttp(object):
    apiurl = 'http://api.yundama.com/api.php'

    def __init__(self, username, password, appid, appkey):
        self.username = username
        self.password = password
        self.appid = appid
        self.appkey = appkey

    def request(self, fields, files=None):
        if not files:
            files = []
        response = self.post_url(self.apiurl, fields, files)
        response = json.loads(response)
        return response

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if response:
            if response['ret'] and response['ret'] < 0:
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if response:
            if response.get('ret', 0) < 0:
                return response.get('ret')
            else:
                return response.get('uid', '')
        else:
            return -9001

    def upload(self, img_content, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'codetype': codetype, 'timeout': str(timeout)}
        files = {'file': img_content}
        response = self.request(data, files)
        if response:
            if response['ret'] and response['ret'] < 0:
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    def decode(self, img_content, codetype, timeout):
        cid = self.upload(img_content, codetype, timeout)
        if cid > 0:
            for i in range(0, timeout):
                res = self.result(cid)
                if res != '':
                    return cid, res
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''

    def report(self, cid):
        data = {'method': 'report', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid), 'flag': '0'}
        response = self.request(data)
        if response:
            return response['ret']
        else:
            return -9001

    def post_url(self, url, fields, files):
        res = requests.post(url, files=files, data=fields)
        return res.text


if __name__ == '__main__':
    username = 'scrapy_yun_zjc'
    password = '123456'
    appid = 7309
    appkey = '15b3e5e8c3004bcea8db86eaed3266b9'
    img_content = requests.get(
        'https://login.sina.com.cn/cgi/pin.php?r=47742300&s=0&p=gz-398b4f196e7af840d0e4337bca592f2510c7').content
    # 验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
    codetype = '1005'
    timeout = 60
    yundama = YDMHttp(username, password, appid, appkey)
    uid = yundama.login()
    balance = yundama.balance()
    print('balance: %s' % balance)
    # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
    cid, result = yundama.decode(img_content, codetype, timeout)
    print('cid: %s, result: %s' % (cid, result))
