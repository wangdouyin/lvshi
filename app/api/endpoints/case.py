"""
案件管理接口
"""
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.case import Case
from app.utils.token import TokenManager
from app.schemas import success, error

router = APIRouter()

# 每页条数
PAGE_SIZE = 20


class CaseListRequest(BaseModel):
    """获取案件列表请求参数"""
    keyword: str = Field("", description="搜索词")
    sort_method: int = Field(0, description="排序依据：0按创建时间 1按完成时间 3按律师最后回复时间", ge=0, le=3)
    sort: int = Field(0, description="0正序 1倒序", ge=0, le=1)
    filter: int = Field(0, description="0全部 1去掉归档 2归档", ge=0, le=2)
    page: int = Field(1, description="页数", ge=1)


def format_timestamp(ts: Optional[int]) -> str:
    """将时间戳转为 年-月-日 时:分 格式"""
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def calc_interval_hours(ts: Optional[int]) -> int:
    """计算时间戳距今多少小时"""
    if not ts:
        return 0
    diff = int(time.time()) - ts
    if diff < 0:
        return 0
    return diff // 3600


@router.post("/case_list")
def case_list(
    request: CaseListRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    获取案件列表

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: 案件列表
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 基础查询：排除已删除的案件
    query = db.query(Case).filter(Case.type != -1)

    # 筛选条件
    if request.filter == 1:
        # 去掉归档
        query = query.filter(Case.type != 1)
    elif request.filter == 2:
        # 只看归档
        query = query.filter(Case.type == 1)

    # 关键词搜索
    if request.keyword:
        keyword = f"%{request.keyword}%"
        query = query.filter(
            (Case.title.like(keyword)) | (Case.introduction.like(keyword))
        )

    # 排序字段
    if request.sort_method == 1:
        sort_field = Case.complete_timestamp
    elif request.sort_method == 3:
        sort_field = Case.lawyer_last_timestamp
    else:
        sort_field = Case.timestamp

    # 排序方向
    if request.sort == 1:
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))

    # 总数
    total = query.count()

    # 分页
    offset = (request.page - 1) * PAGE_SIZE
    cases = query.offset(offset).limit(PAGE_SIZE).all()

    # 判断是否是最后一页
    is_last_page = (offset + len(cases)) >= total

    # 组装返回数据
    data = []
    for i, c in enumerate(cases):
        is_last_item = 1 if (is_last_page and i == len(cases) - 1) else 0
        data.append({
            "case_id": c.case_id,
            "title": c.title or "",
            "introduction": c.introduction or "",
            "timestamp_string": format_timestamp(c.timestamp),
            "lawyer_last_timestamp_string": format_timestamp(c.lawyer_last_timestamp),
            "lawyer_last_timestamp_interval_h": calc_interval_hours(c.lawyer_last_timestamp),
            "progress": c.progress or 0,
            "type": c.type or 0,
            "last_item": is_last_item
        })

    return success(data=data)
