from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view()),

    # 2. 判断用户明是否重复 	/usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),

    # 3. 判断手机号是否重复  mobiles/(?P<mobile>1[3-9]\d{9})/count/
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # 4. 登录 login/
    url(r'^login/$', views.LoginView.as_view(), name="login"),

    # 5. 退出 logout/
    url(r'^logout/$', views.LogOutView.as_view(), name="logout"),

    # 6. 用户中心  info/
    url(r'^info/$', views.UserInfoView.as_view(), name="info"),

    # 7. 保存邮箱  emails/
    url(r'^emails/$', views.EmailView.as_view(), name="email"),

    # 8. 激活邮箱  emails/verification/
    url(r'^emails/verification/$', views.EmailVerifyView.as_view(), name="verify"),
    #
    # # 9. 展示 收货地址 address
    url(r'^address/$', views.AddressView.as_view(), name="address"),
    #
    # # 10. 增加地址  addresses/create/
    url(r'^addresses/create/$', views.AddressAddView.as_view()),

    # 12 . 保存用户记录  browse_histories/
    url(r'^browse_histories/$', views.UserBrowserView.as_view()),


]
