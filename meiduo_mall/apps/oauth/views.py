from django import http
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View

from apps.oauth.models import OAuthQQUser
from apps.users.models import User
from utils.response_code import RETCODE
from QQLoginTool.QQtool import OAuthQQ


# 判断是否绑定openid
def is_bind_openid(openid, request):
    # 判断 openid 在不在 QQ等录表OAuthQQUser
    try:
        qq_user = OAuthQQUser.objects.get(openid=openid)
    except OAuthQQUser.DoesNotExist:
        # 不存在--跳转到 绑定页面
        context = {'openid': openid}
        response = render(request, 'oauth_callback.html', context)
    else:
        # 存在
        user = qq_user.user
        # 1.保持登录装填
        login(request, user)
        # 2. cookie保存用户名
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=14 * 2 * 24 * 3600)

        # 3. 重定向首页
    return response


# http://www.meiduo.site:8000/oauth_callback?code=D185854B840E6F9C3038199FE7735995&state=None
class QQOauthCallbackView(View):
    def get(self, request):
        # 1.code request.GET.get
        code = request.GET.get('code')

        # uri > url
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        # 2. code-->acess_token
        token = oauth.get_access_token(code)

        # 3. acesss_token =--->openid
        openid = oauth.get_open_id(token)

        # 4. 判断是否绑定openid
        response = is_bind_openid(openid, request)

        return response

    def post(self, request):
        # 1.接收参数
        mobile = request.POST.get('mobile')
        pwd = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        openid = request.POST.get('openid')

        # 2. 正则校验
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})

        # 3. 判断 手机号 --存不存在
        # 存在的额=---密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:

            # 不存在--新建用户
            user = User.objects.create_user(username=mobile, password=pwd, mobile=mobile)
        else:

            if not user.check_password(pwd):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 4.绑定openid 操作OAuthQQUser表--新建数据
        OAuthQQUser.objects.create(user=user, openid=openid)


        # 1.保持登录装填
        login(request, user)
        # 2. cookie保存用户名
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=14 * 2 * 24 * 3600)

        # 5.返回首页
        return response


class QQLoginView(View):
    # QQ 登录网址
    def get(self, request):
        # 1.导包 qq登录工具
        from QQLoginTool.QQtool import OAuthQQ

        # 2.实例化对象--->认证的参数
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=None
        )

        # 3.获取qq登录地址 返回给前端 JsonResponse
        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})
