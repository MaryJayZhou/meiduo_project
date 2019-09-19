import re

from django.contrib.auth.backends import ModelBackend

from apps.users.models import User
from meiduo_mall.settings.dev import logger

def get_user_by_account(account):
    try:
        if re.match('^1[345789]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)

    except User.DoesNotExist:
        logger.error('用户对像不再')
    else:
        return user


class  UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        #　校验手机号和用户名
        user = get_user_by_account(username)

        if user.check_password(password):
            return user
