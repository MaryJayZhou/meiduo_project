
from celery_tasks.main import app

@app.task
def send_sms_code_ccp(mobile, sms_code):
    from libs.yuntongxun.sms import CCP

    result = CCP().send_template_sms(mobile, [sms_code, 5],1)

    print(sms_code)

    return result