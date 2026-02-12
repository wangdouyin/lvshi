"""
案件与人物绑定表
"""
from sqlalchemy import Column, Integer

from app.core.database import Base


class AccountCase(Base):
    """
    案件与人物绑定表
    type: 1-客户 2-律师 3-参与者
    """
    __tablename__ = "account_case"

    account_case_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    case_id = Column(Integer, nullable=False, comment="案件表主键")
    account_id = Column(Integer, nullable=False, comment="账号表主键")
    type = Column(Integer, nullable=True, comment="角色类型 1客户 2律师 3参与者")
