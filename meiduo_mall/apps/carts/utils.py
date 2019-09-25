# !/usr/bin/env python
# _*_ coding:utf-8 _*_

# 1.将cookie里面的值  -->合并到---redis 5号数据库
import json
from django_redis import get_redis_connection

from utils.cookiesecret import CookieSecret


def merge_cart_cookie_to_redis(request, user, response):
    # 1. cookie_dict
    cookie_str = request.COOKIES.get('carts')
    if cookie_str:
        cookie_dict = CookieSecret.loads(cookie_str)
    else:
        cookie_dict = {}
        return response

    # 2. redis_dict
    client = get_redis_connection('carts')
    client_data_dict = client.hgetall(user.id)

    redis_dict = {}

    for data in client_data_dict.items():
        sku_id = int(data[0].decode())
        sku_dict = json.loads(data[1].decode())
        redis_dict[sku_id] = sku_dict

    # redis_dict = {int(data[0].decode()):json.loads(data[1].decode()) for data in client_data_dict.items()}


    # 3. 合并 redis_dict.update(cookie_dict)
    redis_dict.update(cookie_dict)

    # 4. 重新插入数据redis
    for sku_id in redis_dict:
        client.hset(user.id, sku_id, json.dumps(redis_dict[sku_id]))

    # 5. 删除cookie
    response.delete_cookie('carts')

    return response
