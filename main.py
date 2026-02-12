"""
FastAPI 应用入口
运行: uvicorn main:app --reload
"""
from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="FastAPI 项目",
    description="FastAPI 应用",
    version="1.0.0",
)

# 注册 API 路由
app.include_router(api_router, prefix="/api")


# @app.get("/")
# def root():
#     return {"message": "Hello World"}


# @app.get("/health")
# def health():
#     return {"status": "ok"}



