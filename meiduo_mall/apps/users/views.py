import json

from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re

from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import User, Address
from apps.users.utils import generate_verify_email_url
from utils.response_code import RETCODE
from django.contrib.auth.mixins import LoginRequiredMixin

from utils.secret import SecretOauth

class UserBrowserView(LoginRequiredMixin, View):
    def post(self, request):

        # 1. 接收参数
        sku_id = json.loads(request.body.decode())['sku_id']

        # 2.校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return http.HttpResponseForbidden('商品不存在!')

        # 3. 链接redis -
        client = get_redis_connection('history')
        redis_key = "history_%d" % request.user.id

        p1 = client.pipeline()

        # 4. 去重
        p1.lrem(redis_key, 0, sku_id)
        # 5. 存
        p1.lpush(redis_key, sku_id)
        # 6. 截取
        p1.ltrim(redis_key, 0, 4)

        p1.execute()

        # 7.存完了
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):

        # 1.从redis 链接--sku_id
        client = get_redis_connection('history')
        # 2. lrange
        sku_ids = client.lrange('history_%d' % request.user.id, 0, -1)

        # 3.通过 sku_ids --skus
        # skus = SKU.objects.filter(id__in=sku_ids)
        # for sku in skus:
        skus_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus_list.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url

            })

        # 4.skus-->前端的数据格式--[{}]

        # 5.返回响应对象
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus_list})


class ChangePwdAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 1.接收参数
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')

        # 2. 校验 判空, 判断正则
        user = request.user

        # 判断密码是否正确
        if not user.check_password(old_password):
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        # 3. 重新设置密码
        user.set_password(new_password)
        user.save()

        # 4.重定向登录页
        response = redirect(reverse('users:login'))

        # 5. 退出登录
        logout(request)

        # 6. 干掉cookie
        response.delete_cookie('username')

        return response


# 10.新增地址
class AddressAddView(LoginRequiredMixin, View):
    def post(self, request):
        # 限制增加个数 不能超过20个
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        # count = request.user.addresses.filter(is_deleted=False).count()
        if count > 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 1. 接收参数 form, json
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验 判空 正则:


        # 3. orm = create() save()
        address = Address.objects.create(
            user=request.user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email,
        )

        # 设置用户的默认地址
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()

        # 4.数据转换—>dict
        address_dict = {
            "id": address.id,
            "title": address.title,

            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


# 9. 展示收货地址
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.根据用户 查询所有地址  filter()
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2.转换前端的数据格式
        adressess_list = []
        for address in addresses:
            adressess_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': adressess_list,
        }

        return render(request, 'user_center_site.html', context)


class EmailVerifyView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.接收参数  request.GET
        token = request.GET.get('token')

        # 解密
        data_dict = SecretOauth().loads(token)

        user_id = data_dict.get('user_id')
        email = data_dict.get('email')

        # 2.校验
        try:
            user = User.objects.get(id=user_id, email=email)
        except Exception as e:
            print(e)
            return http.HttpResponseForbidden('token无效的!')

        # 3. 修改 email_active
        user.email_active = True
        user.save()

        # 4. 返回
        return redirect(reverse('users:info'))


# 7.保存邮箱
class EmailView(LoginRequiredMixin, View):
    def put(self, request):

        # 1.接受参数 json
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 2.校验 正则

        # 3.修改数据 eamil
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            print(e)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱失败!'})

        # 发邮件
        verify_url = generate_verify_email_url(request.user)

        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        # 4.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


# 6. 用户中心
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 方案1.去数据库 查询  个人信息--username(cookie)
        # 方案2. request.user
        user = request.user
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }

        #  render---->jinja2渲染
        # jsonresponse--->v-for Vue

        # 新思路---render-jinja2渲染---let---->Vue渲染

        return render(request, 'user_center_info.html', context)


# 5.退出
class LogOutView(View):
    def get(self, request):
        # 1.清除 登录状态 session
        from django.contrib.auth import logout
        logout(request)
        # 2.清除 username --- cookie
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')
        # 3.重定向到首页
        return response


# 4.登录
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 1.后台接收 解析参数 :3个参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 2. form表单  非表单 ,headers
        # 3. 校验 判空判正则

        # 4. 判断用户名 和密码是否正确--orm User.objects.get(username=username,password=passwod)
        from django.contrib.auth import authenticate, login

        user = authenticate(username=username, password=password)

        # 判断 user是否存在 不存在 代表登录失败
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 保持登登录状态login()
        login(request, user)

        # 判断是否记住登录
        if remembered != 'on':
            #     不记住--会话结束 失效了
            request.session.set_expiry(0)
        else:
            # 记住--2星期
            request.session.set_expiry(None)

        # 操作 next
        next = request.GET.get('next')

        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))

        # 存用户名到 cookie 里面去
        response.set_cookie('username', user.username, max_age=2 * 14 * 24 * 3600)

        # 5.跳转到首页
        return response


# 3.手机号
class MobileCountView(View):
    def get(self, request, mobile):
        # 1.接收参数

        # 2.校验 是否为空 正则

        # 3.务逻辑判断-- 数据库有没有--返回count
        count = User.objects.filter(mobile=mobile).count()

        # 4.返回响应对象
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


# 2.判断用户名是否重复
class UsernameCountView(View):
    def get(self, request, username):
        # 1.接收参数

        # 2.校验 是否为空 正则

        # 3.务逻辑判断-- 数据库有没有--返回count
        count = User.objects.filter(username=username).count()

        # 4.返回响应对象
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


# 1.注册视图
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 1.接收参数 contrl + option(alt) + 单击
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        # # 2.校验 --判空--正则
        # if not all([username, password, password2, mobile]):
        #     return http.HttpResponseForbidden('缺少参数!')
        #
        # # 3.用户名:正则校验—判断重复
        # if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
        #     return http.HttpResponseForbidden('请输入5-20个字符的用户')
        #
        # # 4. 密码:正则校验
        # if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
        #     return http.HttpResponseForbidden('请输入8-20个数字字母')
        #
        # # 5. 两次是否一致
        # if password != password2:
        #     return http.HttpResponseForbidden('两次输入不一致!')
        #
        # # 6.手机号 正则——判断重复
        # if not re.match(r'^1[345789]\d{9}$', mobile):
        #     return http.HttpResponseForbidden('手机号格式有误')
        #
        # # 7.是否勾选同意
        # if allow != 'on':
        #     return http.HttpResponseForbidden('请勾选同意!')
        #
        # # 判断短信验证码 是否正确
        # sms_code = request.POST.get('msg_code')
        #
        # redis_sms_client = get_redis_connection('sms_code')
        # redis_sms_code = redis_sms_client.get('sms_%s' % mobile)
        #
        # if not redis_sms_code:
        #     return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        # redis_sms_client.delete('sms_%s' % mobile)
        #
        # if sms_code != redis_sms_code.decode():
        #     return render(request, 'register.html', {'sms_code_errmsg': '短信验证码不正确!'})

        # 3. 注册
        from apps.users.models import User
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 4. 保持登录状态
        from django.contrib.auth import login
        login(request, user)

        # 4.重定向
        return redirect(reverse('contents:index'))





        # 1.GET—注册页面显示  templates
        # 2.POST 注册功能
        # 判断是否为空!
        # 3.用户名:正则校验—判断重复
        # 4. 密码:正则校验
        # 5. 两次是否一致
        # 6.手机号 正则——判断重复
        # 7.是否勾选同意
        #
        # 8.注册功能 —>入库—mysql—orm—模型类—数据迁移
        # 			    ——>密码—加密解密—>
        # 				django自带权限认证 —User
        #
        # web开发流程
        # 1.先建立模型类—数据迁移
        # 2.接收参数—request.POST
        # 3.校验(非正常用户: 抓包软件filddler charls,postman,爬虫,ajax)
        # 4.注册功能
        # 5.跳转首页 重定向redirect()
