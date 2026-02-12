"""
案件交流表
"""
from sqlalchemy import Column, Integer, Text

from app.core.database import Base


class CaseCommunication(Base):
    """
    案件交流表
    type: 1-客户 2-律师 3-参与者 0-主任
    message_type: 1-文字 2-文件
    """
    __tablename__ = "case_communication"

    case_communication_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    case_id = Column(Integer, nullable=False, comment="案件表主键")
    account_id = Column(Integer, nullable=False, comment="账号表主键")
    type = Column(Integer, nullable=True, comment="角色类型 1客户 2律师 3参与者 0主任")
    message_type = Column(Integer, nullable=True, comment="消息类型 1文字 2文件")
    message = Column(Text, nullable=True, comment="消息")
    timestamp = Column(Integer, nullable=True, comment="创建时间")
