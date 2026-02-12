"""
FastAPI 应用入口
运行: uvicorn main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.openapi.models import SecuritySchemeType
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router

app = FastAPI(
    title="FastAPI 项目",
    description="FastAPI 应用",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,  # 持久化授权信息
    }
)

# 配置全局安全方案，使 Swagger UI 显示 Authorize 按钮
security = HTTPBearer()

# 手动添加安全方案到 OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加安全方案定义
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "输入 Token（无需添加 'Bearer ' 前缀）"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 参数验证错误（Pydantic 422）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一参数校验错误格式"""
    errors = exc.errors()
    # 取第一个错误的信息
    if errors:
        first = errors[0]
        field = first.get("loc", [])[-1] if first.get("loc") else ""
        msg = first.get("msg", "参数错误")
        message = f"{field}: {msg}" if field else msg
    else:
        message = "参数错误"
    return JSONResponse(
        status_code=200,
        content={"code": 422, "message": message, "data": None}
    )


# HTTP 异常（401、403、404 等）
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """统一 HTTP 异常格式"""
    return JSONResponse(
        status_code=200,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None}
    )


# 注册 API 路由
app.include_router(api_router, prefix="/api")


# @app.get("/")
# def root():
#     return {"message": "Hello World"}


# @app.get("/health")
# def health():
#     return {"status": "ok"}



