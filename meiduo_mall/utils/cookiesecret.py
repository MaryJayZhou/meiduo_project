# !/usr/bin/env python
# _*_ coding:utf-8 _*_


import json
import pickle

import base64


class CookieSecret(object):
    # 1.加密
    @classmethod
    def dumps(cls, data):
        # 1.转换类型 --bytes
        pickle_bytes = pickle.dumps(data)
        # 2.转码
        base64_encode = base64.b64encode(pickle_bytes)

        # 3. bytes--str
        return base64_encode.decode()

    # 2.解密
    @classmethod
    def loads(cls, data):
        # 1.解码
        base64_decode = base64.b64decode(data)

        # 2. pickle-->原始数据类型
        data = pickle.loads(base64_decode)

        return data

# data_dict = {
#     1:{
#         2:{
#             "count":3,
#             "selected":True
#         }
#     }
# }
# JSON
# # dict/list ===> json_str
# json_str = json.dumps(data_dict)
#
# # json_str===>dict/list
# json_dict = json.loads(json_str)


# # pickle  所有需要转换的对象 --->转换回去还可以保持以前的类型
# # pickle ===>bytes
# pickle_bytes = pickle.dumps(data_dict)
#
# # bytes====>pickle
# pickle_data = pickle.loads(pickle_bytes)
#
# # base64
# base64_encode = base64.b64encode(pickle_bytes)
#
# print(base64_encode.decode())
#
# base64_decode = base64.b64decode(base64_encode.decode())
#
# print(pickle.loads(base64_decode))
