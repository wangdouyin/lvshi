"""
API 依赖项
用于请求验证、权限检查等
"""
from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

from app.utils.token import TokenManager

# 从请求头 Authorization 中获取 token
auth_header = APIKeyHeader(name="Authorization", auto_error=False)


def get_current_token(authorization: str = Depends(auth_header)) -> str:
    """
    从请求头获取并验证 Token

    :param authorization: 请求头中的 Authorization 值
    :return: token 字符串
    :raises HTTPException: Token 无效时抛出 401 错误
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")

    # 支持 "Bearer token" 和 直接 "token" 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    elif authorization.startswith("bearer "):
        token = authorization[7:]

    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    return token


def get_current_user(authorization: str = Depends(auth_header)) -> dict:
    """
    从请求头获取当前用户信息

    :param authorization: 请求头中的 Authorization 值
    :return: 用户数据字典
    :raises HTTPException: Token 无效时抛出 401 错误
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")

    # 支持 "Bearer token" 和 直接 "token" 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    elif authorization.startswith("bearer "):
        token = authorization[7:]

    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    return user_data
