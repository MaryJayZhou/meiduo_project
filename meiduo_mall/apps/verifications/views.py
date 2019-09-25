from django import http
from django.shortcuts import render
from django.views import View
from apps.verifications import constants
from django_redis import get_redis_connection
import random

from utils.response_code import RETCODE


class SMSCodeView(View):
    def get(self, request, mobile):
        # 1.接收参数 request.GET
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.校验正则

        # 3.对比 图形验证码
        # 3.1链接redis
        image_client = get_redis_connection('verify_image_code')
        # 3.2 取出redis 图形验证码
        redis_img_code = image_client.get('img_%s' % uuid)
        if not redis_img_code:
            return http.JsonResponse({'code': "4001", 'errmsg': '图形验证码失效了'})

        # 3.3 删除图形验证码
        image_client.delete('img_%s' % uuid)

        # 3.4 判断对比 前端的值
        if image_code.lower() != redis_img_code.decode().lower():
            return http.JsonResponse({'code': "4001", 'errmsg': '输入图形验证码有误'})

        # 4. 生成随机 6位
        sms_code = "%06d" % random.randint(0, 999999)

        # 5. 保存redis sms_code
        redis_sms_client = get_redis_connection('sms_code')

        # 1.取出 避免频繁发送短信的 标识
        send_flag = redis_sms_client.get('send_flag_%s' % mobile)
        # 2.如果标识存在 代表 ----已经发过短信了
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # 1.创建管道
        p1 = redis_sms_client.pipeline()
        # 2.添加任务
        p1.setex('sms_%s' % mobile, 300, sms_code)
        p1.setex('send_flag_%s' % mobile, 60, 1)
        # 3.执行
        p1.execute()

        # 6. 发短信--容联云
        from celery_tasks.sms.tasks import send_sms_code_ccp
        send_sms_code_ccp.delay(mobile, sms_code)
        print("原始文件的短信吗:", sms_code)

        # 7.返回响应
        return http.JsonResponse({'code': '0', 'errmsg': '发送短信成功'})


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1.接收参数

        # 2.校验参数 正则 uuid

        # 3.生成图形验证码
        from libs.captcha.captcha import captcha
        text, image_code = captcha.generate_captcha()

        # 4.保存到redis中 为 后面 发送短信验证码做准备
        image_client = get_redis_connection('verify_image_code')
        # image_client.setex('img_%s' % uuid, 300, text)
        image_client.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 5.返回响应对象--->图片二进制流
        return http.HttpResponse(image_code, content_type='image/jpg')
