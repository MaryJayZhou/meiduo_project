# 1. 装包 pip  install itsdangerous
# 2. 导包
# 3.实例化
# 4. 加密解密
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class SecretOauth(object):
    # 1.加密
    def dumps(self, data):
        s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
        result = s.dumps(data)
        return result.decode()

    # 2.解密
    def loads(self, data):
        s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
        result = s.loads(data)
        return result
