from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django import http
import re

from apps.users.models import User
from utils.response_code import RETCODE
#
# 登陆
class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """
        提供登录界面
        :param request: 请求对象
        :return: 登录界面

        """

        # context = {
        #     'username': request.user.username,
        #     'mobile': request.user.mobile,
        #     'email': request.user.email,
        #     'email_active': request.user.email_active
        # }

        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录逻辑
        :param request: 请求对象
        :return: 登录结果
        """
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)

        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或者密码错误'})

        login(request, user)

        if remembered != 'on':
            request.session.set_expiry(0)

        else:
            request.session.set_expiry(None)
        next = request.GET.get('next')

        if next:
            response =redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=2*14*3600)
        return response





# 判断手机号是否重复
class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})

class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})

# 注册
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
    # 接受参数

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        if not all([username, password, password2, mobile]):
            return http.HttpResponseForbidden('缺少参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20个数字字母')

        if password != password2:
            return http.HttpResponseForbidden("两次输入不一致")

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机格式有无')

        if allow != 'on':
            return http.HttpResponseForbidden("请勾选同意")

        user = User.objects.create_user(username=username, password=password, mobile=mobile)
        #
        login(request, user)


        # return http.HttpResponse('首页')
        return redirect(reverse('contents:index'))

        # return redirect('/')
# 退出功能

class LogOutView(View):
    def get(self, request):
        logout(request)
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')

        return response

# 用户中心
from django.contrib.auth.mixins import LoginRequiredMixin


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
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
