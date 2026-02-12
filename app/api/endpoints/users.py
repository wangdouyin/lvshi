"""
用户相关接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import success, error, UserCreateRequest

router = APIRouter()


@router.post("/")
def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """
    创建用户（示例）
    使用 Pydantic 自动验证参数
    """
    # request.name, request.mobile 等已经通过 Pydantic 验证
    return success(
        data={
            "name": request.name,
            "mobile": request.mobile,
            "type": request.type
        },
        message="用户创建成功（示例）"
    )
