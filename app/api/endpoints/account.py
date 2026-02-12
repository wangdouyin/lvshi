"""
账号管理接口
"""
import time
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import re

from app.core.database import get_db
from app.models.account import Account
from app.utils.token import TokenManager
from app.schemas import success, error

router = APIRouter()


class CreateAccountRequest(BaseModel):
    """创建用户请求参数"""
    mobile: str = Field(..., description="手机号", min_length=11, max_length=11)
    name: str = Field(..., description="用户姓名", min_length=1, max_length=50)
    close: int = Field(0, description="关闭状态 0是正常 1是关闭", ge=0, le=1)
    type: int = Field(0, description="类型 1是客户 2是律师 3是参与者 0是主任", ge=0, le=3)

    @validator('mobile')
    def validate_mobile(cls, v):
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v


@router.post("/create_account")
def create_account(
    request: CreateAccountRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    创建用户

    需要在请求头中携带 Token
    
    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {"account_id": 0}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 检查手机号是否已存在
    existing = db.query(Account).filter(Account.mobile == request.mobile).first()
    if existing:
        return error(code=400, message="该手机号已存在")

    # 创建用户
    account = Account(
        mobile=request.mobile,
        name=request.name,
        close=request.close,
        type=request.type,
        sign_up_timestamp=int(time.time())
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return success(
        data={"account_id": account.account_id},
        message="用户创建成功"
    )
