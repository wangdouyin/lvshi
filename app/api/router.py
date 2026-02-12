"""
API 路由汇总
"""
from fastapi import APIRouter

from app.api.endpoints.users import router as users_router
from app.api.endpoints.items import router as items_router
from app.api.endpoints.sms import router as sms_router
from app.api.endpoints.auth import login_router, logout_router
from app.api.endpoints.account import router as account_router

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(login_router, prefix="/login", tags=["登录认证"])
api_router.include_router(logout_router, prefix="/logout", tags=["登录认证"])
api_router.include_router(account_router, prefix="/account", tags=["账号管理"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(items_router, prefix="/items", tags=["物品管理"])
api_router.include_router(sms_router, prefix="/sms", tags=["短信验证码"])
