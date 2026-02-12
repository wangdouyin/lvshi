"""
短信验证码接口
"""
import random
import time
import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.sms import Sms
from app.core.aliyun.sms_code import send_sms
from app.schemas import success, error

router = APIRouter()


class SmsRequest(BaseModel):
    """短信请求参数"""
    mobile: str


@router.post("/")
def send_sms_code(request: SmsRequest, db: Session = Depends(get_db)):
    """
    发送短信验证码
    
    :param request: 请求参数 {"mobile": "手机号"}
    :param db: 数据库会话
    :return: {"code": 0, "message": "string", "data": {}}
    """
    mobile = request.mobile
    
    # 验证手机号格式（中国大陆手机号：1开头，11位数字）
    if not re.match(r'^1[3-9]\d{9}$', mobile):
        return error(code=400, message="手机号格式错误")
    
    current_time = int(time.time())
    one_minute_ago = current_time - 60

    # 查询1分钟内是否有发送成功的记录
    recent_sms = db.query(Sms).filter(
        Sms.mobile == mobile,
        Sms.type == 1,  # 假设 type=1 表示发送成功
        Sms.timestamp >= one_minute_ago,
        Sms.timestamp <= current_time
    ).first()

    if recent_sms:
        return error(code=429, message="发送过于频繁，请稍后再试")

    # 生成6位随机验证码
    code = str(random.randint(100000, 999999))
    
    # 调用阿里云发送短信
    response = send_sms(mobile, code)
    
    # 判断是否发送成功
    is_success = response is not None and hasattr(response, "code") and response.code == "OK"
    
    # 只有发送成功时才插入数据库
    if is_success:
        sms_record = Sms(
            mobile=mobile,
            sms_code=code,
            timestamp=current_time,
            type=1
        )
        db.add(sms_record)
        db.commit()
        db.refresh(sms_record)
        return success(message="短信发送成功")
    else:
        # 发送失败，不插入数据库，直接返回错误
        error_message = getattr(response, "message", "短信发送失败") if response else "短信发送失败"
        return error(code=500, message=error_message)
