from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
import json

from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.cookiesecret import CookieSecret
from utils.response_code import RETCODE


class CartsView(View):
    def post(self, request):
        # 1. 接收 非form - json参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2.校验---
        # 2.1 sku
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品不存在!')

        # 2.2 判断整数
        try:
            count = int(count)
        except:
            return http.HttpResponseForbidden('count 类型不是整型!')

        # 2.3 判断是否是bool
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('selected 类型不是布尔类型!')

        # 3.判断是否登录
        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
        if user.is_authenticated:
            # 3.1 登录---redis存储

            # 3.2 --链接redis
            redis_carts_client = get_redis_connection('carts')
            # 3.3 --查询该用户的 所有购物车数据
            client_data = redis_carts_client.hgetall(user.id)

            print("判断之前", client_data)

            # 3.4 判断 是否有: {b'1': b'{"count": 1, "selected": true}'}
            if str(sku_id).encode() in client_data:
                print(client_data)
                bytes_carts = client_data[str(sku_id).encode()]
                str_carts = bytes_carts.decode()
                dict_carts = json.loads(str_carts)

                # 有: count+=1
                dict_carts['count'] += count

                # 重新 覆盖 以前的个数
                redis_carts_client.hset(user.id, sku_id, json.dumps(dict_carts))
            else:
                # 没有 直接新增 {'count':count,'selected':selected}
                redis_carts_client.hset(user.id, sku_id, json.dumps({"count": count, "selected": selected}))

        else:
            # 3.2 未登录---cookie加密存储
            print('没登录---redis存储')

            # 3.2.1 获取cookie中所有购物车数据
            cookie_str = request.COOKIES.get('carts')

            # 3.2.2 解密
            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

            # 3.2.3 判断 是否存在
            if sku_id in carts_dict:
                # 存在 累加
                origi_count = carts_dict[sku_id]['count']
                count += origi_count

            # 不存 新增
            carts_dict[sku_id] = {'count': count, 'selected': selected}

            # 3.2.4 加密--->str
            dumps_str = CookieSecret.dumps(carts_dict)

            # 重新插入cookie
            response.set_cookie('carts', dumps_str, max_age=14 * 24 * 3600)

        # 4.返回响应
        return response

    def get(self, request):

        # 1.判断是否登录
        user = request.user
        if user.is_authenticated:
            # 登录 --获取数据--redis
            # 1.链接
            client = get_redis_connection('carts')

            # 2.hgetall  {b'1': b'{"count": 1, "selected": true}'}
            carts_redis = client.hgetall(user.id)

            carts_dict = {}
            for key,value in carts_redis.items():
                cart_key = int(key.decode())
                cart_redis_dict = json.loads(value.decode())
                carts_dict[cart_key] = cart_redis_dict

            # carts_dict = {int(key.decode()):json.loads(value.decode()) for key,value in carts_redis.items()}

        else:
            # 没有登录---cookie
            cookie_str = request.COOKIES.get('carts')
            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

        # 从购物车数据 获取 所有sku_ids
        # sku_ids ===skus
        sku_ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),

                'count': carts_dict[sku.id]['count'],
                'selected': str(carts_dict[sku.id]['selected']),
                'amount': str(sku.price * carts_dict[sku.id]['count']),

            })

        context = {
            'cart_skus': cart_skus
        }
        print(cart_skus)

        return render(request, 'cart.html', context)

    def put(self, request):
        """修改购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        try:
            sku =SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品sku_id不存在')

            # 判断用户是否登录
        user = request.user
        # 接收cookie最后的数据
        cookie_cart_str = ""
        if user.is_authenticated:
            # 1.链接 redis
            carts_redis_client = get_redis_connection('carts')
            # 2.覆盖redis以前的数据
            new_data = {'count': count, 'selected': selected}
            carts_redis_client.hset(user.id, sku_id, json.dumps(new_data))
        else:
            # 用户未登录，修改cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = CookieSecret.loads(cart_str)
            else:
                cart_dict = {}

            # 覆盖以前的数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 转换成 密文数据
            cookie_cart_str = CookieSecret.dumps(cart_dict)

        cart_sku = {
            'id': sku_id,
            'count': count,
            'selected': selected,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': sku.price,
            'amount': sku.price * count,
        }

        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        if not user.is_authenticated:
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cookie_cart_str, max_age=24 * 30 * 3600)
        return response

    def delete(self,request):
        sku_id = json.loads(request.body.decode()).get('sku_id')

        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('商品不存在')

        user = request.user
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
        if user is not None and user.is_authenticated:
            # 用户未登录，删除redis购物车
            carts_redis_client = get_redis_connection('carts')

            # 根据用户id 删除商品sku
            carts_redis_client.hdel(user.id, sku_id)

            # 删除结束后，没有响应的数据，只需要响应状态码即可

        else:
            # 用户未登录，删除cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 转成明文
                cart_dict = CookieSecret.loads(cart_str)

                if sku_id in cart_dict:
                    # 删除数据
                    del cart_dict[sku_id]
                    # 将字典转成密文
                    cookie_cart_str = CookieSecret.dumps(cart_dict)

                    response.set_cookie('carts', cookie_cart_str, max_age=24 * 30 * 3600)

                return response