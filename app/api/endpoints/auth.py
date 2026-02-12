"""
认证相关接口
"""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import re

from app.core.database import get_db
from app.models.account import Account
from app.models.sms import Sms
from app.utils.token import TokenManager
from app.schemas import success, error

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求参数"""
    mobile: str = Field(..., description="手机号", min_length=11, max_length=11)
    code: str = Field(..., description="验证码", min_length=6, max_length=6)
    
    @validator('mobile')
    def validate_mobile(cls, v):
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v
    
    @validator('code')
    def validate_code(cls, v):
        """验证验证码格式"""
        if not v.isdigit():
            raise ValueError('验证码必须是6位数字')
        return v


@router.post("/")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    短信验证码登录
    
    :param request: 请求参数 {"mobile": "手机号", "code": "验证码"}
    :param db: 数据库会话
    :return: {"code": 0, "message": "string", "data": {"token": "string"}}
    """
    mobile = request.mobile
    code = request.code
    current_time = int(time.time())
    five_minutes_ago = current_time - 300  # 5分钟 = 300秒
    
    # 1. 查询验证码记录
    sms_record = db.query(Sms).filter(
        Sms.mobile == mobile,
        Sms.sms_code == code,
        Sms.type == 1,  # 未使用
        Sms.timestamp >= five_minutes_ago  # 5分钟内
    ).order_by(Sms.timestamp.desc()).first()
    
    if not sms_record:
        return error(code=400, message="验证码错误或已过期")
    
    # 2. 验证码验证成功，立即标记为已使用
    sms_record.type = 2
    db.commit()
    
    # 3. 查询账号是否存在
    account = db.query(Account).filter(
        Account.mobile == mobile
    ).first()
    
    if not account:
        return error(code=404, message="该手机号不是系统用户")
    
    # 4. 检查账号是否被关闭
    if account.close == 1:
        return error(code=403, message="账号已被关闭，请联系管理员")
    
    # 5. 生成 token
    token = TokenManager.generate(
        account_id=account.account_id,
        account_type=account.type,
        extra_data={
            "mobile": account.mobile,
            "name": account.name
        }
    )
    
    # 6. 返回结果
    return success(
        data={"token": token},
        message="登录成功"
    )
