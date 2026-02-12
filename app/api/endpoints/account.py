"""
账号管理接口
"""
import time
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import re

from app.core.database import get_db
from app.models.account import Account
from app.utils.token import TokenManager
from app.schemas import success, error

# 每页条数
PAGE_SIZE = 20

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


class UpdateAccountRequest(BaseModel):
    """编辑用户请求参数"""
    account_id: int = Field(..., description="用户ID")
    mobile: str = Field(..., description="手机号", min_length=11, max_length=11)
    name: str = Field(..., description="用户姓名", min_length=1, max_length=50)
    type: int = Field(0, description="类型 1是客户 2是律师 3是参与者 0是主任", ge=0, le=3)

    @validator('mobile')
    def validate_mobile(cls, v):
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v


@router.post("/update_account")
def update_account(
    request: UpdateAccountRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    编辑用户

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 查询用户是否存在
    account = db.query(Account).filter(Account.account_id == request.account_id).first()
    if not account:
        return error(code=404, message="用户不存在")

    # 如果修改了手机号，检查新手机号是否已被其他用户使用
    if request.mobile != account.mobile:
        existing = db.query(Account).filter(
            Account.mobile == request.mobile,
            Account.account_id != request.account_id
        ).first()
        if existing:
            return error(code=400, message="该手机号已被其他用户使用")

    # 更新用户信息
    account.mobile = request.mobile
    account.name = request.name
    account.type = request.type
    db.commit()

    return success(message="用户编辑成功")


class GetAccountRequest(BaseModel):
    """获取用户请求参数"""
    account_id: int = Field(..., description="用户ID")


@router.post("/get_account")
def get_account(
    request: GetAccountRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    根据ID获取用户

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: 用户信息
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 查询用户
    account = db.query(Account).filter(Account.account_id == request.account_id).first()
    if not account:
        return error(code=404, message="用户不存在")

    # 格式化注册时间
    sign_up_str = ""
    if account.sign_up_timestamp:
        sign_up_str = datetime.fromtimestamp(account.sign_up_timestamp).strftime("%Y-%m-%d %H:%M")

    return success(data={
        "account_id": account.account_id,
        "name": account.name or "",
        "mobile": account.mobile or "",
        "sign_up_timestamp_string": sign_up_str,
        "close": account.close or 0,
        "type": account.type or 0
    })


class GetAccountListRequest(BaseModel):
    """获取用户列表请求参数"""
    page: int = Field(1, description="页数", ge=1)
    type_array: List[int] = Field(..., description="用户类型数组，如 [0,1,2,3]")


@router.post("/get_account_list")
def get_account_list(
    request: GetAccountListRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    获取用户列表

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: 用户列表
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 查询条件：按类型筛选
    query = db.query(Account).filter(Account.type.in_(request.type_array))

    # 按注册时间倒序
    query = query.order_by(Account.account_id.desc())

    # 总数
    total = query.count()

    # 分页
    offset = (request.page - 1) * PAGE_SIZE
    accounts = query.offset(offset).limit(PAGE_SIZE).all()

    # 判断是否是最后一页
    is_last_page = (offset + len(accounts)) >= total

    # 组装返回数据
    data = []
    for i, a in enumerate(accounts):
        is_last_item = 1 if (is_last_page and i == len(accounts) - 1) else 0
        sign_up_str = ""
        if a.sign_up_timestamp:
            sign_up_str = datetime.fromtimestamp(a.sign_up_timestamp).strftime("%Y-%m-%d %H:%M")
        data.append({
            "account_id": a.account_id,
            "name": a.name or "",
            "mobile": a.mobile or "",
            "sign_up_timestamp_string": sign_up_str,
            "close": a.close or 0,
            "type": a.type or 0,
            "last_item": is_last_item
        })

    return success(data=data)
