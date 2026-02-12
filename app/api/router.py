"""
API 路由汇总
"""
from fastapi import APIRouter

from app.api.endpoints import users, items

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(items.router, prefix="/items", tags=["物品管理"])
