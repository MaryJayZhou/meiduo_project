from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^qq/login/$', views.QQLoginView.as_view()),

    # oauth_callback 回调地址
    url(r'^oauth_callback/$', views.QQOauthCallbackView.as_view()),

]
