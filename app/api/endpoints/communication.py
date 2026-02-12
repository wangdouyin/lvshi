"""
案件交流接口
"""
import time
from datetime import datetime
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import asc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.case import Case
from app.models.case_communication import CaseCommunication
from app.models.account import Account
from app.models.account_case import AccountCase
from app.utils.token import TokenManager
from app.schemas import success, error

router = APIRouter()


class CaseCommunicationRequest(BaseModel):
    """交流大厅请求参数"""
    case_id: int = Field(..., description="案件ID")


@router.post("/case_communication")
def case_communication(
    request: CaseCommunicationRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    交流大厅获取数据

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: 交流记录列表
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    # 当前用户ID
    current_account_id = user_data.get("account_id")

    # 查询交流记录，关联 account 表获取姓名，按时间正序
    records = db.query(CaseCommunication, Account.name).outerjoin(
        Account, CaseCommunication.account_id == Account.account_id
    ).filter(
        CaseCommunication.case_id == request.case_id
    ).order_by(asc(CaseCommunication.timestamp)).all()

    # 组装返回数据
    data = []
    for record, name in records:
        timestamp_str = ""
        if record.timestamp:
            timestamp_str = datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%M")

        data.append({
            "case_communication_id": record.case_communication_id,
            "message_type": record.message_type or 0,
            "message": record.message or "",
            "account_id": record.account_id,
            "name": name or "",
            "is_me": 1 if record.account_id == current_account_id else 0,
            "type": record.type or 0,
            "timestamp_string": timestamp_str
        })

    return success(data=data)


class CaseCommunicationMessageRequest(BaseModel):
    """交流消息提交请求参数"""
    case_id: int = Field(..., description="案件ID")
    message: str = Field(..., description="消息内容", min_length=1)
    message_type: int = Field(..., description="消息类型 1文字 2文件", ge=1, le=2)


@router.post("/case_communication_message")
def case_communication_message(
    request: CaseCommunicationMessageRequest,
    db: Session = Depends(get_db),
    token: str = Header(..., description="登录时获取的Token")
):
    """
    交流消息提交

    :param request: 请求参数
    :param db: 数据库会话
    :param token: 认证Token
    :return: {"code": 0, "message": "string", "data": {"case_communication_id": 0}}
    """
    # 验证 token
    user_data = TokenManager.verify(token)
    if not user_data:
        return error(code=401, message="Token无效或已过期")

    current_account_id = user_data.get("account_id")
    current_time = int(time.time())

    # 查询案件是否存在
    case = db.query(Case).filter(Case.case_id == request.case_id).first()
    if not case:
        return error(code=404, message="案件不存在")

    # 查询当前用户在该案件中的角色
    binding = db.query(AccountCase).filter(
        AccountCase.case_id == request.case_id,
        AccountCase.account_id == current_account_id
    ).first()

    # 获取用户在account表中的type（主任为0）
    account = db.query(Account).filter(Account.account_id == current_account_id).first()
    if binding:
        role_type = binding.type
    elif account and account.type == 0:
        role_type = 0  # 主任
    else:
        return error(code=403, message="您不是该案件的参与人员")

    # 创建交流记录
    record = CaseCommunication(
        case_id=request.case_id,
        account_id=current_account_id,
        type=role_type,
        message_type=request.message_type,
        message=request.message,
        timestamp=current_time
    )
    db.add(record)

    # 如果是律师发消息，更新案件的律师最后回复时间
    if role_type == 2:
        case.lawyer_last_timestamp = current_time

    db.commit()
    db.refresh(record)

    return success(
        data={"case_communication_id": record.case_communication_id},
        message="消息发送成功"
    )
