"""
案件管理接口
"""
import time
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.case import Case
from app.models.account_case import AccountCase
from app.models.account import Account
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


class AccountCaseItem(BaseModel):
    """案件绑定人员"""
    account_id: int = Field(..., description="账号表主键")
    type: int = Field(..., description="角色类型 1是客户 2是律师 3是参与者", ge=1, le=3)


class CreateCaseRequest(BaseModel):
    """创建案件请求参数"""
    title: str = Field(..., description="标题", min_length=1, max_length=200)
    introduction: str = Field("", description="简介")
    account_case: List[AccountCaseItem] = Field(..., description="案件绑定人员列表")


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

    # 获取当前用户 ID
    account_id = user_data.get("account_id")

    # 查询该用户关联的案件ID
    user_case_ids = db.query(AccountCase.case_id).filter(
        AccountCase.account_id == account_id
    ).subquery()

    # 基础查询：只查该用户关联的案件，排除已删除的
    query = db.query(Case).filter(
        Case.case_id.in_(user_case_ids),
        Case.type != -1
    )

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


@router.post("/create_case")
def create_case(
    request: CreateCaseRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    创建案件

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {"case_id": 0}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    current_time = int(time.time())

    # 1. 创建案件
    case = Case(
        title=request.title,
        introduction=request.introduction,
        timestamp=current_time,
        progress=1,  # 默认进行中
        type=0       # 默认正常
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # 2. 创建案件与人物绑定关系
    for item in request.account_case:
        account_case = AccountCase(
            case_id=case.case_id,
            account_id=item.account_id,
            type=item.type
        )
        db.add(account_case)
    db.commit()

    return success(
        data={"case_id": case.case_id},
        message="案件创建成功"
    )


class UpdateCaseRequest(BaseModel):
    """更新案件请求参数"""
    case_id: int = Field(..., description="案件ID")
    title: str = Field(..., description="标题", min_length=1, max_length=200)
    introduction: str = Field("", description="简介")
    progress: int = Field(1, description="进度 1进行中 2完成", ge=1, le=2)
    account_case: List[AccountCaseItem] = Field(..., description="案件绑定人员列表")


@router.post("/update_case")
def update_case(
    request: UpdateCaseRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    更新编辑案件数据

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 1. 查询案件是否存在
    case = db.query(Case).filter(Case.case_id == request.case_id).first()
    if not case:
        return error(code=404, message="案件不存在")

    # 2. 更新案件信息
    case.title = request.title
    case.introduction = request.introduction
    case.progress = request.progress

    # 如果进度改为完成，记录完成时间
    if request.progress == 2 and not case.complete_timestamp:
        case.complete_timestamp = int(time.time())

    # 3. 删除旧的绑定关系
    db.query(AccountCase).filter(AccountCase.case_id == request.case_id).delete()

    # 4. 创建新的绑定关系
    for item in request.account_case:
        account_case = AccountCase(
            case_id=request.case_id,
            account_id=item.account_id,
            type=item.type
        )
        db.add(account_case)

    db.commit()

    return success(message="案件更新成功")


class CaseTypeRequest(BaseModel):
    """案件状态变更请求参数"""
    case_id: int = Field(..., description="案件ID")
    type: int = Field(..., description="状态：-1删除 0正常 1归档", ge=-1, le=1)


@router.post("/case_type")
def case_type(
    request: CaseTypeRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    案件状态变更（删除/正常/归档）

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 查询案件
    case = db.query(Case).filter(Case.case_id == request.case_id).first()
    if not case:
        return error(code=404, message="案件不存在")

    # 已删除的案件不允许再操作
    if case.type == -1:
        return error(code=400, message="该案件已删除，无法操作")

    # 不允许设置为当前相同的状态
    if case.type == request.type:
        type_map = {-1: "删除", 0: "正常", 1: "归档"}
        return error(code=400, message=f"案件已是{type_map.get(request.type, '')}状态")

    # 更新状态
    case.type = request.type
    db.commit()

    type_map = {-1: "删除", 0: "恢复正常", 1: "归档"}
    return success(message=f"案件{type_map.get(request.type, '')}成功")


class CaseDetailsRequest(BaseModel):
    """案件详情请求参数"""
    case_id: int = Field(..., description="案件ID")


@router.post("/case_details")
def case_details(
    request: CaseDetailsRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    获取案件详情

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: 案件详情数据
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 查询案件
    case = db.query(Case).filter(Case.case_id == request.case_id).first()
    if not case:
        return error(code=404, message="案件不存在")

    # 查询案件绑定的人员，关联 account 表获取姓名
    bindings = db.query(AccountCase, Account.name).join(
        Account, AccountCase.account_id == Account.account_id
    ).filter(
        AccountCase.case_id == request.case_id
    ).all()

    # 组装绑定人员数据
    account_case_list = []
    for binding, name in bindings:
        account_case_list.append({
            "account_id": binding.account_id,
            "type": binding.type,
            "name": name or ""
        })

    # 组装返回数据
    data = {
        "case_id": case.case_id,
        "title": case.title or "",
        "introduction": case.introduction or "",
        "timestamp_string": format_timestamp(case.timestamp),
        "complete_timestamp_string": format_timestamp(case.complete_timestamp),
        "lawyer_last_timestamp_string": format_timestamp(case.lawyer_last_timestamp),
        "lawyer_last_timestamp_interval_h": calc_interval_hours(case.lawyer_last_timestamp),
        "progress": case.progress or 0,
        "type": case.type or 0,
        "account_case": account_case_list
    }

    return success(data=data)
