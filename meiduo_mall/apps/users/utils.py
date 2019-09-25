import re

from django.conf import settings
from django.contrib.auth.backends import ModelBackend

from apps.users.models import User
from meiduo_mall.settings.dev import logger

def generate_verify_email_url(user):
    # http://www.meiduo.site:8000/emails/verification/?token=eyJhbGciOiJIUzUxMiIsImlhdCI6MTU2NjE5ODk4MywiZXhwIjoxNTY2MjAyNTgzfQ.eyJ1c2VyX2lkIjo2LCJlbWFpbCI6ImxpdWNoZW5nZmVuZzY2NjZAMTYzLmNvbSJ9.okIKKAHjeskFild3EZeK3034N2r0vMb_tvUaVA7h4qPdfxmsDG4JvzXsTLl2_98Ln6rpWN4EmAdrdthZeG2DdQ
    host_url = settings.EMAIL_ACTIVE_URL
    data_dict = {
        'user_id':user.id,
        'email':user.email
    }
    from utils.secret import SecretOauth
    dumps_params = SecretOauth().dumps(data_dict)
    verify_url = host_url + "?token=" + dumps_params

    return verify_url


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
