#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/14 14:20
# @Author  : zhangpeng
# @Site    : redis_pool.py
# @File    :  创建redis连接模块


import redis


class RedisPool(object):
    """
    用于redis存储链接
    """

    def __init__(self, db=0):
        # self.__redis_conn = redis.Redis(host='127.0.0.1', port=63790, db=0)
        __pool1 = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, db=db)
        self.__redis_conn = redis.Redis(connection_pool=__pool1)
        self.save_key = 'cookie'  # 默认cookie键
        self.login_cookie = 'login_cookie'  # 取队列cookie
        self.logout_cookie = 'logout_cookie'  # 取队列cookie
        self.failure_queue = 'failure_queue'  # 失败队列
        self.T = 3000  # 过期时间

    def rsave(self, value):
        self.__redis_conn.set(name=self.save_key, value=value, ex=self.T)
        return True

    def rget(self, cookie_type):
        return self.__redis_conn.rpop(cookie_type)

    def redis_con(self):
        return self.__redis_conn

    def request_queue(self, dkey):
        return self.__redis_conn.hget('store', dkey)

    def get_cookie(self, cookie_type):
        return self.__redis_conn.rpop(cookie_type)

    def failure_save(self, value):
        return self.__redis_conn.lpush(self.failure_queue, value)

    def ltrim(self, cookie_type):
        self.__redis_conn.ltrim(cookie_type, 0, 200)

    def hget(self, cookie_type, key):
        self.__redis_conn.hget(cookie_type, key)

    def hgetall(self, cookie_type):
        return self.__redis_conn.hgetall(cookie_type)


if __name__ == '__main__':
    pass
    # pgdb = RedisPool()
    # pgdb.rget()
