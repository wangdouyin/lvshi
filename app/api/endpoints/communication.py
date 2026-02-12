"""
案件交流接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import asc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.case_communication import CaseCommunication
from app.models.account import Account
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
